"""Offline proof: real HA client + loopback HTTP + extracted Espressif C logic.
No hardware, Home Assistant server, or real network dataset is contacted.
"""
import argparse, asyncio, ctypes, json, pathlib, subprocess, sys, unittest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer
from python_otbr_api import OTBR, ActiveDataSet, Timestamp

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--prepared", type=pathlib.Path, required=True)
parser.add_argument("--idf", type=pathlib.Path, required=True)
args, test_args = parser.parse_known_args()
ROOT = args.prepared.resolve() / "contract"
ROOT.mkdir(exist_ok=True)
IDF = args.idf.resolve()
SERVER = args.prepared.resolve() / "firmware/low-power/generated/esp_ot_br_server"
C = SERVER / "src/esp_br_web.c"
BASE = SERVER / "src/esp_br_web_base.c"
ORIGINAL = args.prepared.resolve() / "upstream-original/src/esp_br_web.c"



def function(source, signature):
    start=source.index(signature)
    opening=source.index('{',start)
    depth=1; pos=opening+1
    while depth:
        depth += (source[pos]=='{')-(source[pos]=='}'); pos+=1
    return source[start:pos]


def compile_logic(name, source):
    prelude=r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "cJSON.h"
#include "openthread/dataset.h"
typedef int esp_err_t;
#define ESP_OK 0
#define ESP_FAIL -1
#define ESP_ERR_INVALID_ARG -2
#define WEB_TAG "test"
#define BASE_TAG "test"
#define ESP_OT_REST_CONTENT_TYPE_JSON "application/json"
#define HTTPD_404 "404 Not Found"
#define ESP_LOGD(...) ((void)0)
#define ESP_RETURN_ON_FALSE(c,e,...) do {if (!(c)) return (e);}while(0)
#define ESP_RETURN_ON_ERROR(c,...) do {int e=(c);if(e) return e;}while(0)
#define ESP_GOTO_ON_ERROR(c,label,...) do {int e=(c);if(e) {ret=e;goto label;}}while(0)
typedef struct {int status; const char *uri; char body[1024];} httpd_req_t;
static int httpd_resp_set_status(httpd_req_t *r,const char *s){r->status=atoi(s);return 0;}
static int httpd_resp_set_type(httpd_req_t *r,const char *s){return 0;}
static int httpd_resp_sendstr(httpd_req_t *r,const char *s){snprintf(r->body,sizeof(r->body),"%s",s);return 0;}
static int string_to_hex(const char *s,uint8_t *out,size_t n){
 if(strlen(s)!=n*2)return ESP_ERR_INVALID_ARG;
 for(size_t i=0;i<n;i++){unsigned int x;if(sscanf(s+i*2,"%2x",&x)!=1)return ESP_ERR_INVALID_ARG;out[i]=x;}
 return 0;
}
otError otIp6PrefixFromString(const char *aString,otIp6Prefix *aPrefix){return OT_ERROR_PARSE;}
'''
    chunks=[prelude]
    for sig in ['static cJSON *resource_status(', 'static esp_err_t httpd_send_packet(', 'static esp_err_t NOT_FOUND_handler(']:
        chunks.append(function(source,sig))
    base=BASE.read_text()
    for sig in ['esp_err_t Json2Timestamp(', 'esp_err_t Json2SecurityPolicy(', 'esp_err_t Json2ActiveDataset(']:
        chunks.append(function(base,sig))
    chunks.append(r'''
static httpd_req_t request;
static otOperationalDataset parsed;
int missing_http_status(void){memset(&request,0,sizeof(request));request.status=200;request.uri="/api/actions";NOT_FOUND_handler(&request);return request.status;}
const char *missing_body(void){return request.body;}
unsigned int parse_dataset(const char *text){
 memset(&parsed,0,sizeof(parsed));cJSON *j=cJSON_Parse(text);int error=Json2ActiveDataset(j,&parsed);cJSON_Delete(j);if(error)return 0x80000000u;
 return parsed.mComponents.mIsNetworkNamePresent | (parsed.mComponents.mIsChannelPresent<<1) | (parsed.mComponents.mIsActiveTimestampPresent<<2);
}
const char *parsed_name(void){return parsed.mNetworkName.m8;}
unsigned int parsed_channel(void){return parsed.mChannel;}
uint64_t parsed_seconds(void){return parsed.mActiveTimestamp.mSeconds;}
''')
    file=ROOT/f'{name}.c';file.write_text('\n\n'.join(chunks))
    lib=ROOT/f'{name}.dylib' if sys.platform=='darwin' else ROOT/f'{name}.so'
    cj=IDF/'components/json/cJSON'
    subprocess.run(['clang','-std=c11',*(['-dynamiclib'] if sys.platform=='darwin' else ['-shared','-fPIC']),'-Wall','-Wextra','-Wno-unused-parameter',str(file),str(cj/'cJSON.c'),'-I'+str(cj),'-I'+str(IDF/'components/openthread/openthread/include'),'-o',str(lib)],check=True)
    obj=ctypes.CDLL(str(lib));obj.missing_body.restype=ctypes.c_char_p;obj.parsed_name.restype=ctypes.c_char_p
    obj.parse_dataset.argtypes=[ctypes.c_char_p];obj.parse_dataset.restype=ctypes.c_uint;obj.parsed_seconds.restype=ctypes.c_uint64
    return obj


class Contract(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        upstream=ORIGINAL.read_text()
        cls.original=compile_logic('upstream_logic',upstream)
        cls.fixed=compile_logic('fixed_logic',C.read_text())
        cls.proofs=[]

    async def exercise(self,lib):
        requests=[];flags=[]
        async def handler(req):
            body=await req.text();requests.append({'method':req.method,'path':req.path,'body':body})
            if req.path=='/api/actions':
                status=lib.missing_http_status()
                return web.Response(status=status,text=lib.missing_body().decode(),content_type='application/json')
            if req.path=='/node/ba-id':return web.json_response('11223344556677889900aabbccddeeff')
            if req.path=='/node/ext-address':return web.json_response('1122334455667788')
            if req.path=='/node/dataset/active':
                if req.method=='GET':return web.Response(text='0003000014',content_type='text/plain')
                if req.headers.get('Content-Type','').startswith('text/plain'):
                    return web.Response(status=200)
                flags.append(lib.parse_dataset(body.encode()))
                return web.Response(status=201)
            return web.Response(status=404)
        app=web.Application();app.router.add_route('*','/{path:.*}',handler)
        async with TestServer(app) as server, ClientSession() as session:
            api=OTBR(str(server.make_url('')).rstrip('/'),session,10)
            self.assertEqual(await api.get_border_agent_id(),bytes.fromhex('11223344556677889900aabbccddeeff'))
            self.assertEqual(await api.get_extended_address(),bytes.fromhex('1122334455667788'))
            self.assertEqual(await api.get_active_dataset_tlvs(),bytes.fromhex('0003000014'))
            await api.create_active_dataset(ActiveDataSet(network_name='synthetic-thread',channel=20,active_timestamp=Timestamp(seconds=123,ticks=0,authoritative=False)))
            await api.set_active_dataset_tlvs(bytes.fromhex('0003000014'))
        return requests,flags

    async def test_01_upstream_bug_is_reproduced(self):
        self.assertEqual(self.original.missing_http_status(),200)
        requests,flags=await self.exercise(self.original)
        self.assertEqual(flags,[0], 'Upstream unexpectedly consumed camelCase fields')
        self.proofs.append({'variant':'unmodified-upstream','unknown_url_http':200,'parsed_field_flags':flags,'requests':requests})

    async def test_02_fixed_handler_preserves_dataset_fields(self):
        self.assertEqual(self.fixed.missing_http_status(),404)
        requests,flags=await self.exercise(self.fixed)
        self.assertEqual(flags,[7])
        self.assertEqual(self.fixed.parsed_name(),b'synthetic-thread')
        self.assertEqual(self.fixed.parsed_channel(),20)
        self.assertEqual(self.fixed.parsed_seconds(),123)
        self.proofs.append({'variant':'fixed-404','unknown_url_http':404,'parsed_field_flags':flags,'requests':requests})

    @classmethod
    def tearDownClass(cls):
        (ROOT/'contract-results.json').write_text(json.dumps(cls.proofs,indent=2)+'\n')

if __name__=='__main__':unittest.main(argv=[sys.argv[0], *test_args], verbosity=2)
