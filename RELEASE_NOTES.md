# Local Data Masking Tool 2.0

Version 2.0 is a security and usability redesign of the original masking and aggregation tool.

## Highlights

- New blue, scrollable desktop interface with a full-width data preview.
- Familiar batch workflow for adding and removing dimensions and metrics.
- Keyed HMAC-SHA256 masking with a fresh random key per job.
- Password-encrypted `.maskvault` files stored separately from masked data.
- Authorized Restore workflow with strict vault matching.
- Restored Excel files include both `Restored_Data` and a filterable `Mapper` tab.
- Optional AI Context Layer for explaining dimension meaning without revealing sensitive values.

## Masking workflow

- Load CSV, XLSX, or XLS data.
- Batch-select available columns.
- Add fields as dimensions or numeric metrics.
- Choose dimensions to mask.
- Configure metric aggregation.
- Optionally add an AI context blurb.
- Save masked output and the encrypted vault to different folders.

## Output formats

Excel masked output:

- `Masked_Data`
- Optional `Context_Layer`

Excel restored output:

- `Restored_Data`
- `Mapper` with Dimension, Masked Value, and Original Value

CSV jobs create companion `_context.txt` and `_mapper.csv` files when applicable.

## Security changes

- Removed selectable plain MD5, SHA-256, and SHA-512 hashing.
- Removed combined data-and-key workbooks.
- Vault passwords are never stored.
- Wrong passwords and mismatched vaults fail without producing misleading restored output.
- Masked output and vault folders must be different.

## Usability improvements

- Larger active tab with clearer selected state.
- Crisp blue-and-white visual system.
- Full-width preview and vertically organized workflow.
- Master vertical scrollbar for smaller screens and display scaling.
- Show/hide password controls.
- Automatic context prompts based on selected dimensions.
- Windows `.bat` launchers now use plain Command Prompt commands and no longer invoke PowerShell with an execution-policy bypass.

## Compatibility

- Windows desktop
- macOS desktop
- Python 3.10 or newer
- CSV and Excel input
- CSV and XLSX output

macOS includes double-click `.command` launchers and `.sh` Terminal alternatives. Gatekeeper approval may be required on first launch.

## Upgrade notes

Version 1.3 key workbooks are not the same as version 2.0 encrypted vaults. Create a new masking job in version 2.0 to use the Restore, Mapper, and Context Layer features.

Existing version 2.0 output must be regenerated to receive features added after its original creation, such as the Context Layer or Mapper tab.
