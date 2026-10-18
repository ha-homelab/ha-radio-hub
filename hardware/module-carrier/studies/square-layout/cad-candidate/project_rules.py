"""Persist MC1 routing rules after pcbnew.SaveBoard rewrites project defaults.

Standalone pcbnew board loading does not attach KiCad's project net settings;
SaveBoard may therefore replace them with defaults. All native-write scripts
call this helper afterwards. No severity or DRC-exclusion settings are changed.
"""
import json
from pathlib import Path
from design import parts

def restore_project_rules(root=None):
    root=Path(root) if root else Path(__file__).resolve().parent
    path=root/'mc1.kicad_pro'
    project=json.loads(path.read_text()) if path.exists() else {}
    project.setdefault('meta',{}).update(filename='mc1.kicad_pro',version=1)
    settings=project.setdefault('board',{}).setdefault('design_settings',{})
    settings.setdefault('rules',{}).update(min_clearance=.2,min_track_width=.2,min_via_diameter=.8,min_through_hole_diameter=.4,min_copper_edge_clearance=.5)
    netsettings=project.setdefault('net_settings',{})
    netsettings['meta']={'version':5}
    classes={n['name']:n for n in netsettings.get('classes',[])}
    default=classes.get('Default',{})
    default.update(name='Default',clearance=.2,track_width=.25,via_diameter=.8,via_drill=.4,priority=2147483647)
    power=classes.get('Power',dict(default))
    power.update(name='Power',clearance=.2,track_width=.8,via_diameter=.8,via_drill=.4,priority=0)
    netsettings['classes']=[default,power]
    nets=sorted({net for part in parts for net in part['pins'].values() if net and (net.startswith('+') or net=='GND')})
    netsettings['netclass_patterns']=[{'netclass':'Power','pattern':'/'+net} for net in nets]
    netsettings['netclass_assignments']={}
    path.write_text(json.dumps(project,indent=2)+'\n')

if __name__=='__main__':restore_project_rules()
