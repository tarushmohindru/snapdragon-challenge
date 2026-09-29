ClipTrail Snapdragon inventory (no installation or model inference)

1. Extract this zip on the Snapdragon HP PC.
2. Open native Windows PowerShell in the extracted directory.
3. Run:
   powershell.exe -NoProfile -File .\collect_inventory.ps1
4. Return evidence\inventory-<timestamp>\inventory.json to the participant.

If the device's script policy blocks the command, return the error. This script
does not change execution policy, require admin, install anything or use network.
It collects model/chip/RAM/Windows/build/driver and runtime metadata, not personal
files, serial numbers, screen contents, usernames or network identifiers.

This is stage 1 only. The inference bundle and exact ARM64 dependencies follow
after their artifacts have been obtained and validated. Nothing here establishes
NPU use. Qualcomm/Snapdragon names or provider installation are not execution proof.
