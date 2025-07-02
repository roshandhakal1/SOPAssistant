# Google Drive SOP Setup Guide

This guide will help you set up clickable Google Drive links for your SOP documents in the SOP Assistant.

## Quick Start - Interactive Mode

For the easiest setup, run:

```bash
python generate_gdrive_metadata.py --interactive --directory ./documents
```

This will:
1. Find all your SOP files
2. Prompt you to enter the Google Drive URL for each one
3. Automatically create the metadata files

## Batch Mode (Recommended for Many Files)

If you have many SOPs, use batch mode:

### Step 1: Generate CSV Template
```bash
python generate_gdrive_metadata.py --sample-csv
```

This creates `sop_gdrive_mapping.csv` with all your SOP files listed.

### Step 2: Fill in Google Drive URLs
Open `sop_gdrive_mapping.csv` and add the Google Drive URLs:

```csv
filename,gdrive_url
Quality Control Procedures.docx,https://drive.google.com/file/d/1ABC123/view
Manufacturing SOP Rev3.pdf,https://drive.google.com/file/d/1DEF456/view
Safety Guidelines.doc,https://drive.google.com/file/d/1GHI789/view
```

### Step 3: Process the CSV
```bash
python generate_gdrive_metadata.py --csv sop_gdrive_mapping.csv
```

## Check Your Work

List all created metadata files:
```bash
python generate_gdrive_metadata.py --list
```

## Supported Google Drive URL Formats

The script accepts any of these formats:
- `https://drive.google.com/file/d/FILE_ID/view`
- `https://drive.google.com/file/d/FILE_ID/edit`
- `https://drive.google.com/open?id=FILE_ID`
- `https://docs.google.com/document/d/FILE_ID`

## What Happens After Setup

1. Each SOP file gets a companion `.gdrive_metadata` file
2. When you reprocess documents (if needed), the vector database includes Google Drive links
3. When the AI references an SOP, users see a clickable link like:
   ```
   📄 Quality Control Procedures.docx [Open in Google Drive]
   ```

## Troubleshooting

**Problem**: "No SOP files found"
- **Solution**: Check the `--directory` path. Default is `./documents`

**Problem**: "Could not extract Google Drive ID"
- **Solution**: Make sure the URL contains the file ID. Copy the "Share" link from Google Drive.

**Problem**: Metadata file already exists
- **Solution**: Use `--overwrite` flag to replace existing files

## Complete Example

```bash
# 1. Check what files are in your documents folder
ls ./documents

# 2. Generate metadata interactively
python generate_gdrive_metadata.py --interactive --directory ./documents

# 3. Verify everything was created
python generate_gdrive_metadata.py --list --directory ./documents
```

## Next Steps

After creating metadata files:
1. The SOP Assistant will automatically use Google Drive links
2. No need to reprocess documents - the system detects metadata files automatically
3. Test by asking the AI about an SOP and clicking the reference link

---

**Need Help?** Run `python generate_gdrive_metadata.py` without arguments to see all available options.