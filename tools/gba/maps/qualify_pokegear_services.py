"""Build/run headless gear qualification; no GUI emulator is started."""
from pathlib import Path
import subprocess,json,hashlib
from PIL import Image
root=Path(__file__).resolve().parents[3];src=root/'tools/vendor/gba/opening-house-work';out=root/'tools/vendor/gba/pokegear-services-evidence';out.mkdir(exist_ok=True)
tc=root/'tools/vendor/gba/arm-gnu-toolchain-14.2.rel1-darwin-arm64-arm-none-eabi'
names=set(['ApocGear_ClaimGift', 'ApocGear_EnsureState', 'ApocGear_FieldStep', 'ApocGear_GetNote', 'ApocGear_GiveMapCard', 'ApocGear_QueueCall', 'ApocGear_RecordCall', 'ApocGear_Register', 'ApocGear_RematchReady', 'ApocGear_Seal', 'ApocGear_SetGift', 'ApocGear_SetNote', 'ApocGear_SetRematchContact', 'ArePlayerFieldControlsLocked', 'CB2_Overworld', 'CountTotalItemQuantityInBag', 'FindTaskIdByFunc', 'FlagGet', 'GetDayOfWeek', 'LoadGameSave', 'MapProof_ReadState', 'Task_NewGameBirchSpeech_ChooseGender', 'TrySavingData', 'VarGet', 'gLocalTime', 'gMain', 'gMapProofState', 'gObjectEvents', 'gSaveBlock2Ptr', 'gSaveBlock3Ptr', 'gSaveblock3', 'sApp', 'sCall', 'sMapRegion', 'sMapX', 'sMapY', 'sNoteMode', 'sPhoneHistory', 'sQuizChoice', 'sQuizResult', 'sRadioText', 'sStartMenuCursorPos', 'sZoom'])
nm=subprocess.check_output([str(tc/'bin/arm-none-eabi-nm'),str(src/'pokeemerald.elf')],text=True)
syms={v[2]:v[0] for l in nm.splitlines() if len(v:=l.split())==3 and v[2] in names};assert not names-set(syms)
(out/'symbols.txt').write_text(''.join(f'{n} {a}\n' for n,a in sorted(syms.items())))
subprocess.run(['cc','-I/opt/homebrew/opt/mgba/include',str(root/'tools/gba/maps/pokegear_services_runtime.c'),'-L/opt/homebrew/opt/mgba/lib','-lmgba','-o','/tmp/gear-services-runtime'],check=True)
with (out/'runtime.jsonl').open('w') as log:
 subprocess.run(['/tmp/gear-services-runtime',str(src/'pokeemerald.gba'),str(out/'symbols.txt'),str(root/'tools/vendor/gba/pokegear-modern-evidence/continue-gear-settings.sav'),str(out)],stdout=log,check=True)
evidence=root/'gba/art/pokegear-services/evidence';evidence.mkdir(exist_ok=True)
for p in out.glob('*.ppm'):Image.open(p).save(evidence/(p.stem+'.png'))
(evidence/'runtime.txt').write_bytes((out/'runtime.jsonl').read_bytes())
print('service qualification passed')
