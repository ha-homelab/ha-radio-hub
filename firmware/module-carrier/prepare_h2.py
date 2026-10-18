#!/usr/bin/env python3
"""Prepare H2 RCP on ROM UART23/24; carrier isolates DevKit USB bridge R7."""
import argparse
from pathlib import Path
from prepare import load_legacy

def prepare(output: Path,idf: Path) -> Path:
    result=load_legacy("prepare_h2").prepare(output,idf)
    path=result/"sdkconfig.defaults"
    text=path.read_text()
    for setting in ("CONFIG_OPENTHREAD_UART_RX_PIN=23", "CONFIG_OPENTHREAD_UART_TX_PIN=24"):
        if text.count(setting)!=1:
            raise RuntimeError("Pinned RCP defaults changed")
    path.write_text(text)
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    parser.add_argument("--idf",type=Path,required=True)
    args=parser.parse_args()
    print(prepare(args.output,args.idf))
