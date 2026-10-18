#include <cassert>
#include <deque>
#include <vector>
#include <string>
#include "transport.h"
using namespace esphome::wk2132_uart;

struct Device {
  uint8_t regs[2][16]{};
  uint8_t page=0, error=0;
  bool fail_read=false, fail_write=false, fail_reg=false, race=false, post_read_error=false, busy=false;
  std::deque<uint8_t> rx,tx;
  std::vector<uint8_t> transmitted;
  Device() { regs[0][0]=0x80; }
  void pause() {}
  bool reg_read(uint8_t r,uint8_t &v) {
    if(fail_reg)return false;
    if(r==Transport::SPAGE){v=page;return true;}
    if(r==Transport::GENA){v=regs[0][0];return true;}
    if(page){v=regs[1][r];return true;}
    if(r==Transport::RFCNT){v=rx.size()&255;if(race&&rx.empty()){rx.push_back(91);race=false;}return true;}
    if(r==Transport::TFCNT){v=tx.size()&255;return true;}
    if(r==Transport::FSR){v=error|(rx.empty()?0:8)|(tx.empty()?0:4)|(tx.size()==256?2:0)|(busy?1:0);return true;}
    v=regs[0][r];return true;
  }
  bool reg_write(uint8_t r,uint8_t v) {
    if(fail_reg)return false;
    if(r==Transport::SPAGE){page=v;return true;}
    if(r==Transport::GENA){regs[0][r]=v|0x80;return true;}
    regs[page][r]=v;return true;
  }
  bool fifo_read(uint8_t *p,size_t n) {
    if(fail_read)return false;
    assert(n<=rx.size()&&n<=64);
    for(size_t i=0;i<n;++i){p[i]=rx.front();rx.pop_front();}
    if(post_read_error)error=0x80;
    return true;
  }
  bool fifo_write(const uint8_t *p,size_t n) {
    assert(n<=256-tx.size()&&n<=64);
    if(fail_write){tx.push_back(p[0]);return false;}
    for(size_t i=0;i<n;++i)tx.push_back(p[i]);
    return true;
  }
  void drain(){while(!tx.empty()){transmitted.push_back(tx.front());tx.pop_front();}}
};
int main(int argc,char **argv) {
  assert(argc==2);std::string name=argv[1];Device io;Transport transport;
  assert(transport.initialize(io));
  if(name=="init") {
    assert(io.regs[1][4]==0&&io.regs[1][5]==7&&io.regs[1][6]==0);
    assert(io.regs[0][4]==3&&io.regs[0][5]==0&&io.regs[0][6]==15);
    io.regs[0][4]=0;assert(!transport.health(io));assert(transport.fault()==Fault::IDENTITY);
  } else if(name=="large_tx") {
    std::vector<uint8_t> bytes(1537);for(size_t i=0;i<bytes.size();++i)bytes[i]=i;
    assert(transport.enqueue(bytes.data(),bytes.size()));
    for(int i=0;i<10;++i){transport.service(io);io.drain();}
    transport.service(io);assert(transport.idle());assert(io.transmitted==bytes);
  } else if(name=="backpressure") {
    io.tx.resize(253,5);uint8_t bytes[70]{};
    assert(transport.enqueue(bytes,70));transport.service(io);
    assert(io.tx.size()==256&&transport.pending()==67);
    transport.service(io);assert(transport.pending()==67);
    io.drain();transport.service(io);assert(transport.pending()==0);
  } else if(name=="full_rx") {
    for(int i=0;i<256;++i)io.rx.push_back(i);
    transport.service(io);assert(transport.available()==256);
    uint8_t data[256];assert(transport.receive(data,256));
    for(int i=0;i<256;++i)assert(data[i]==uint8_t(i));
  } else if(name=="count_race") {
    io.race=true;transport.service(io);assert(transport.available()==1);
    uint8_t value;assert(transport.receive(&value,1)&&value==91);
  } else if(name=="read_error") {
    io.rx.push_back(1);io.fail_read=true;transport.service(io);
    assert(transport.fault()==Fault::IO&&transport.available()==0);
  } else if(name=="write_error") {
    uint8_t data[100]{};transport.enqueue(data,100);io.fail_write=true;transport.service(io);
    assert(transport.fault()==Fault::IO&&transport.pending()==0&&io.tx.size()==1);
    io.fail_write=false;transport.service(io);assert(io.tx.size()==1);
  } else if(name=="line_errors") {
    for(uint8_t e:{0x10,0x20,0x40,0x80}){
      Device d;Transport t;assert(t.initialize(d));d.rx.push_back(9);t.service(d);
      assert(t.available()==1);d.error=e;t.service(d);assert(t.fault()==Fault::LINE&&t.available()==0);
    }
  } else if(name=="post_read_error") {
    io.rx.push_back(1);io.post_read_error=true;transport.service(io);
    assert(transport.fault()==Fault::LINE&&transport.available()==0);
  } else if(name=="rx_overflow") {
    for(int i=0;i<9;++i){io.rx.resize(256,1);transport.service(io);}
    assert(transport.fault()==Fault::RX_OVERFLOW&&transport.available()==0);
  } else if(name=="tx_overflow") {
    std::vector<uint8_t> bytes(2049);assert(!transport.enqueue(bytes.data(),bytes.size()));
    assert(transport.fault()==Fault::TX_OVERFLOW&&transport.pending()==0&&io.tx.empty());
  } else if(name=="busy") {
    io.busy=true;transport.service(io);assert(!transport.idle());
    io.busy=false;transport.service(io);assert(transport.idle());
  } else if(name=="reg_error") {
    io.fail_reg=true;transport.service(io);assert(transport.fault()==Fault::IO);
  } else if(name=="peek_partial") {
    io.rx.push_back(22);transport.service(io);uint8_t data[2]={0,99};
    assert(transport.receive(data,1,true)&&data[0]==22&&transport.available()==1);
    assert(!transport.receive(data,2)&&data[1]==99&&transport.available()==1);
  } else assert(false);
}
