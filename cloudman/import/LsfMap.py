'''This map will contain the LSFGROUP and Experiment(aka accounting group) and unix_group from the LSFWEB for the accounting group we create 
group in the Cloudman.This experiment names has been found out by logging into the
 lsfweb interface and getting the experiment name and unix group for those which i
 am not able to found out i have added the unix group as it-dep-pes-ps  
 '''
lsf_group_map = {
		'u_ALEPH' :{'EXPERIMENT':'aleph','UNIXGROUP': 'xu'},
		'u_ALICE' :{'EXPERIMENT':'alice','UNIXGROUP': 'z2'},
		'u_AMS'   :{'EXPERIMENT':'ams','UNIXGROUP': 'va'},
		'u_AMSP'  :{'EXPERIMENT':'ams','UNIXGROUP': 'va'},
		'u_ATLAS' :{'EXPERIMENT':'atlas','UNIXGROUP': 'zp'},
		'u_ATLCASTORACL':{'EXPERIMENT':'atlas','UNIXGROUP': 'zp'},
		'u_ATLDEDICATED'  :{'EXPERIMENT':'atlas','UNIXGROUP': 'zp'},
		'u_C3'    :{'EXPERIMENT':'c3','UNIXGROUP': 'c3'},
		'u_CAST'  :{'EXPERIMENT':'cast','UNIXGROUP': 'vh'},
		'u_CMS'   :{'EXPERIMENT':'cms','UNIXGROUP': 'zh'},
		'u_CMSALCA':{'EXPERIMENT':'cms','UNIXGROUP': 'zh'},
		'u_CMSCOMM':{'EXPERIMENT':'cms','UNIXGROUP': 'zh'},
		'u_CMSPHYS':{'EXPERIMENT':'cms','UNIXGROUP': 'zh'},
		'u_CMST3' :{'EXPERIMENT':'cms','UNIXGROUP': 'zh'},
		'u_COMPASS':{'EXPERIMENT':'compass','UNIXGROUP': 'vy'},
		'u_DELPHI':{'EXPERIMENT':'delphi','UNIXGROUP': 'xx'},
		'u_DIRAC' :{'EXPERIMENT':'dirac','UNIXGROUP': 'vk'},
		'u_DTEAM' :{'EXPERIMENT':'grid','UNIXGROUP': ''},
		'u_FLUKARP':{'EXPERIMENT':'fluka_rp','UNIXGROUP': 'hc'},
		'u_GEANT4':{'EXPERIMENT':'geant4','UNIXGROUP': 'zb'},
		'u_GEAR'  :{'EXPERIMENT':'gear','UNIXGROUP': 'ge'},
		'u_HARP'  :{'EXPERIMENT':'harp','UNIXGROUP': 'uh'},
		'u_HARPD' :{'EXPERIMENT':'harp','UNIXGROUP': 'uh'},
		'u_ILC'   :{'EXPERIMENT':'ilc','UNIXGROUP': 'zf'},
		'u_ISOLDE':{'EXPERIMENT':'isolde','UNIXGROUP': 'z6'},
		'u_ITDC'  :{'EXPERIMENT':'other','UNIXGROUP': ''},
		'u_L3'    :{'EXPERIMENT':'l3','UNIXGROUP': 'xv'},
		'u_LHCB'   :{'EXPERIMENT':'lhcb','UNIXGROUP': 'z5'},
		'u_LHCBCAF':{'EXPERIMENT':'lhcb','UNIXGROUP': 'z5'},
		'u_LHCBT3':{'EXPERIMENT':'lhcb','UNIXGROUP': 'z5'},
		'u_LHCF'  :{'EXPERIMENT':'lhcf','UNIXGROUP': 'zc'},
		'u_NA38NA50':{'EXPERIMENT':'na38/na50','UNIXGROUP': 'wf'},
		'u_NA45'  :{'EXPERIMENT':'na45','UNIXGROUP': 'yt'},
		'u_NA48'  :{'EXPERIMENT':'na48','UNIXGROUP': 'vl'},
		'u_NA49'  :{'EXPERIMENT':'na49','UNIXGROUP': 'vp'},
		'u_NA61'  :{'EXPERIMENT':'na61','UNIXGROUP': 'wj'},
		'u_NOMAD' :{'EXPERIMENT':'wa96','UNIXGROUP': 'xh'},
		'u_NTOF'  :{'EXPERIMENT':'ntof','UNIXGROUP': 'za'},
		'u_OPAL'  :{'EXPERIMENT':'opal','UNIXGROUP': 'ws'},
		'u_OPERA' :{'EXPERIMENT':'opera','UNIXGROUP': 'vo'},
		'u_PARC'  :{'EXPERIMENT':'other','UNIXGROUP': ''},
		'u_SFT'   :{'EXPERIMENT':'sft','UNIXGROUP': 'sf'},
		'u_SLDIV' :{'EXPERIMENT':'sl_div','UNIXGROUP': 'si'},
		'u_THEORY':{'EXPERIMENT':'theory','UNIXGROUP': 't3'},
		'u_TOTEM' :{'EXPERIMENT':'totem','UNIXGROUP': 'zj'},
		'u_UNOSAT':{'EXPERIMENT':'unosat','UNIXGROUP': 'un'}
		}

##In this hostpartition hepspec is there
lsf_dedicated_group_hepspec = {
		'u_CMS':{'CMSCAF':6101},
		'u_LHCB':{'LHCBT3':630,'LHCBINTER':368}			
			}
