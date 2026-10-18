#!/usr/bin/env python3
"""Prepare IDF5.5.5 H2 RCP with carrier RX4/TX5, keeping USB-UART23/24 free."""
import argparse
from pathlib import Path
from prepare import load_legacy

def prepare(output: Path,idf: Path) -> Path:
    result=load_legacy("prepare_h2").prepare(output,idf)
    path=result/"sdkconfig.defaults"
    text=path.read_text()
    for old,new in (("CONFIG_OPENTHREAD_UART_RX_PIN=23","CONFIG_OPENTHREAD_UART_RX_PIN=4"),
                    ("CONFIG_OPENTHREAD_UART_TX_PIN=24","CONFIG_OPENTHREAD_UART_TX_PIN=5")):
        if text.count(old)!=1:
            raise RuntimeError("Pinned RCP defaults changed")
        text=text.replace(old,new)
    path.write_text(text)
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--idf",type=Path,required=True)
    args=parser.parse_args()
    print(prepare(args.output,args.idf))
