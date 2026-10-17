import unittest
from routing_metrics import measure
from validate import child,children,net_name

class RoutingMetricsTests(unittest.TestCase):
 def board(self,via=False):
  def pad(ref,num,x):
   return ['footprint',['property','Reference',ref],['at','0','0'],['pad',num,'smd','rect',['at',str(x),'0'],['size','0.1','0.1'],['layers','F.Cu'],['net','eth_txp']]]
  def trace(a,b,layer):return ['segment',['start',str(a),'0'],['end',str(b),'0'],['layer',layer],['net','eth_txp']]
  b=['kicad_pcb',pad('U4','2',0),pad('J1','2',10),trace(0,5,'F.Cu'),trace(5,10,'F.Cu')]
  # A long terminated stub must not increase source-to-destination length.
  b.append(['segment',['start','5','0'],['end','5','20'],['layer','F.Cu'],['net','eth_txp']])
  if via:
   child(b[4],'layer')[1]='B.Cu';child(child(b[2],'pad'),'layers')[1]='B.Cu'
   b.append(['via',['at','5','0'],['net','eth_txp']])
  return b
 def test_branch_does_not_distort_pair_length(self):
  p=measure(self.board(),child,children,net_name)['paths']['eth_txp']
  self.assertEqual(p['track_mm'],10)
  self.assertEqual(p['total_net_track_mm'],30)
  self.assertEqual(p['via_transitions'],0)
 def test_via_and_layer_change_reported(self):
  p=measure(self.board(True),child,children,net_name)['paths']['eth_txp']
  self.assertEqual(p['track_mm'],10)
  self.assertEqual(p['via_transitions'],1)
  self.assertEqual(p['layers'],['B.Cu','F.Cu'])
if __name__=='__main__':unittest.main()
