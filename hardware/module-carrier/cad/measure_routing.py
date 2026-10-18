#!/usr/bin/env python3
"""Measure native track centreline lengths (not airwire estimates), excluding pours."""
import argparse,hashlib,json
from pathlib import Path
import pcbnew as pcb
ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
b=pcb.LoadBoard(str(a.board));nets={}
for t in b.GetTracks():
 n=t.GetNetname();d=nets.setdefault(n,dict(track_length_mm=0,via_count=0,segment_count=0,by_layer_mm={}))
 if isinstance(t,pcb.PCB_VIA):d['via_count']+=1;continue
 length=pcb.ToMM(t.GetLength());d['track_length_mm']+=length;d['segment_count']+=1;layer=b.GetLayerName(t.GetLayer());d['by_layer_mm'][layer]=d['by_layer_mm'].get(layer,0)+length
for d in nets.values():
 d['track_length_mm']=round(d['track_length_mm'],4);d['by_layer_mm']={k:round(v,4) for k,v in d['by_layer_mm'].items()}
r=dict(board_sha256=hashlib.sha256(a.board.read_bytes()).hexdigest(),measurement='Native routed copper centreline lengths; vias counted separately; filled zones and module internal traces excluded',total_track_length_mm=round(sum(d['track_length_mm'] for d in nets.values()),4),total_vias=sum(d['via_count'] for d in nets.values()),total_segments=sum(d['segment_count'] for d in nets.values()),per_net=dict(sorted(nets.items())))
a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='per_net'}))
