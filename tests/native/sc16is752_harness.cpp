#include <cassert>
#include <deque>
#include <vector>
#include <string>
#include "registers.h"
using namespace esphome::sc16is752_uart;

struct Device {
  uint8_t regs[16]{};
  uint8_t dll=0,dlh=0,efr=0;
  uint8_t error=0,capacity=64;
  bool connected=true;
  std::deque<uint8_t> rx;
  std::vector<uint8_t> tx;
  void pause() {}
  uint8_t read(uint8_t r) {
    if (!connected) return 0xff;
    if (r==LSR) return error | (tx.empty()?0x60:0) | (rx.empty()?0:1);
    if (r==RXLVL) return rx.size();
    if (r==TXLVL) return capacity;
    if (r==FIFO) { assert(!rx.empty()); auto b=rx.front();rx.pop_front();return b; }
    return regs[r];
  }
  void write(uint8_t r,uint8_t v) {
    if (!connected) return;
    if (r==IOCONTROL && v==8) { for(auto &b:regs)b=0; rx.clear();tx.clear();return; }
    if (regs[LCR]==0xbf && r==FCR) {efr=v;return;}
    if (regs[LCR]&0x80) {
      if(r==FIFO){dll=v;return;}
      if(r==IER){dlh=v;return;}
    }
    if(r==FIFO){assert(tx.size()<64);tx.push_back(v);return;}
    regs[r]=v;
  }
};
int main(int argc,char **argv) {
  assert(argc==2); std::string name=argv[1]; Device io;
  if(name=="divisor") {
    assert(divisor(1843200,115200)==1);assert(divisor(3686400,115200)==2);
    assert(divisor(14745600,256000)==0);assert(divisor(1000,0)==0);
    assert(command(RXLVL,true)==0xc8);assert(command(FIFO,false)==0x00);
    assert(command(SPR,true)==0xb8);
  } else if(name=="init") {
    assert(initialize(io,3686400,115200)); assert(io.dll==2 && io.dlh==0);
    assert(io.regs[LCR]==3 && io.regs[IER]==5 && io.regs[FCR]==1 && io.efr==16);
    io.connected=false;assert(!initialize(io,1843200,115200));
  } else {
    assert(initialize(io,1843200,115200));
    std::vector<uint8_t> received;std::deque<uint8_t> send;
    for(unsigned i=0;i<64;++i)io.rx.push_back(i);
    for(unsigned i=0;i<100;++i)send.push_back(i+100);
    auto take=[&](uint8_t b){received.push_back(b);return true;};
    auto put=[&](uint8_t &b){if(send.empty())return false;b=send.front();send.pop_front();return true;};
    if(name=="duplex") {
      assert(service(io,take,put)); assert(received.size()==64 && io.tx.size()==64 && send.size()==36);
      for(unsigned i=0;i<64;++i){assert(received[i]==i);assert(io.tx[i]==uint8_t(i+100));}
      io.tx.clear();assert(service(io,take,put));assert(io.tx.size()==36 && send.empty());
    } else if(name=="backpressure") {
      io.capacity=0;assert(service(io,take,put));assert(io.tx.empty() && send.size()==100);
    } else if(name=="rx_overflow") {
      assert(!service(io,[](uint8_t){return false;},put));assert(io.tx.empty());
    } else if(name=="line_error") {
      for(uint8_t error:{2,4,8,16,128}){io.error=error;assert(!service(io,take,put));}
      assert(received.empty() && io.tx.empty());
    } else if(name=="invalid_level") {
      io.rx.push_back(64);assert(!service(io,take,put));
      io.rx.clear();io.capacity=255;assert(!service(io,take,put));
    } else assert(false);
  }
}
