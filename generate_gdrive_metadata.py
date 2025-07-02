#!/usr/bin/env python3
"""
Google Drive Metadata Generator for SOP Documents

This script helps you generate .gdrive_metadata files for your SOP documents
so that when the AI references them, users can click to open the actual SOPs in Google Drive.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

class GDriveMetadataGenerator:
    def __init__(self, sop_directory: str):
        """
        Initialize the metadata generator
        
        Args:
            sop_directory: Path to directory containing SOP documents
        """
        self.sop_directory = Path(sop_directory)
        self.supported_extensions = ['.doc', '.docx', '.pdf', '.txt']
        
    def extract_gdrive_id_from_url(self, gdrive_url: str) -> str:
        """
        Extract Google Drive file ID from various Google Drive URL formats
        
        Args:
            gdrive_url: Google Drive URL in various formats
            
        Returns:
            Google Drive file ID
        """
        # Handle different Google Drive URL formats
        patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)',           # /file/d/ID/view
            r'id=([a-zA-Z0-9-_]+)',                # ?id=ID
            r'/d/([a-zA-Z0-9-_]+)',                # /d/ID
            r'drive\.google\.com.*?([a-zA-Z0-9-_]{25,})',  # General pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, gdrive_url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract Google Drive ID from URL: {gdrive_url}")
    
    def create_gdrive_link(self, file_id: str, link_type: str = "view") -> str:
        """
        Create a standardized Google Drive link
        
        Args:
            file_id: Google Drive file ID
            link_type: "view" or "edit"
            
        Returns:
            Standardized Google Drive URL
        """
        if link_type == "edit":
            return f"https://drive.google.com/file/d/{file_id}/edit"
        else:
            return f"https://drive.google.com/file/d/{file_id}/view"
    
    def find_sop_files(self) -> List[Path]:
        """
        Find all SOP files in the directory
        
        Returns:
            List of SOP file paths
        """
        sop_files = []
        for ext in self.supported_extensions:
            sop_files.extend(self.sop_directory.glob(f"*{ext}"))
        
        return sorted(sop_files)
    
    def create_metadata_file(self, sop_file: Path, gdrive_url: str, overwrite: bool = False) -> bool:
        """
        Create .gdrive_metadata file for a specific SOP
        
        Args:
            sop_file: Path to the SOP document
            gdrive_url: Google Drive URL for the document
            overwrite: Whether to overwrite existing metadata files
            
        Returns:
            True if file was created, False if skipped
        """
        metadata_file = Path(str(sop_file) + '.gdrive_metadata')
        
        if metadata_file.exists() and not overwrite:
            print(f"⚠️  Metadata file already exists: {metadata_file.name} (use --overwrite to replace)")
            return False
        
        try:
            gdrive_id = self.extract_gdrive_id_from_url(gdrive_url)
            gdrive_link = self.create_gdrive_link(gdrive_id, "view")
            
            metadata = {
                "gdrive_id": gdrive_id,
                "gdrive_link": gdrive_link,
                "original_filename": sop_file.name,
                "created_by": "gdrive_metadata_generator"
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Created: {metadata_file.name}")
            return True
            
        except ValueError as e:
            print(f"❌ Error processing {sop_file.name}: {e}")
            return False
    
    def interactive_mapping(self) -> None:
        """
        Interactive mode to map SOP files to Google Drive URLs
        """
        sop_files = self.find_sop_files()
        
        if not sop_files:
            print(f"❌ No SOP files found in {self.sop_directory}")
            print(f"Supported extensions: {', '.join(self.supported_extensions)}")
            return
        
        print(f"📁 Found {len(sop_files)} SOP files in {self.sop_directory}")
        print("\n🔗 Interactive Google Drive URL Mapping")
        print("=" * 50)
        
        for i, sop_file in enumerate(sop_files, 1):
            print(f"\n📄 [{i}/{len(sop_files)}] {sop_file.name}")
            
            # Check if metadata file already exists
            metadata_file = Path(str(sop_file) + '.gdrive_metadata')
            if metadata_file.exists():
                print("   ℹ️  Metadata file already exists")
                choice = input("   Continue anyway? (y/N): ").strip().lower()
                if choice != 'y':
                    print("   ⏭️  Skipped")
                    continue
            
            while True:
                gdrive_url = input("   🔗 Enter Google Drive URL (or 'skip' to skip, 'quit' to exit): ").strip()
                
                if gdrive_url.lower() == 'quit':
                    print("\n👋 Exiting...")
                    return
                
                if gdrive_url.lower() == 'skip':
                    print("   ⏭️  Skipped")
                    break
                
                if not gdrive_url:
                    print("   ⚠️  Please enter a URL or 'skip'")
                    continue
                
                if 'drive.google.com' not in gdrive_url:
                    print("   ⚠️  Please enter a valid Google Drive URL")
                    continue
                
                success = self.create_metadata_file(sop_file, gdrive_url, overwrite=True)
                if success:
                    break
                else:
                    print("   ⚠️  Please try again with a valid Google Drive URL")
        
        print(f"\n✅ Metadata generation complete!")
        print(f"📋 Next steps:")
        print(f"   1. Reprocess your documents to update the vector database")
        print(f"   2. The AI will now show clickable Google Drive links when referencing SOPs")
    
    def batch_mapping_from_csv(self, csv_file: str) -> None:
        """
        Create metadata files from a CSV mapping file
        
        CSV format: filename,gdrive_url
        """
        import csv
        
        csv_path = Path(csv_file)
        if not csv_path.exists():
            print(f"❌ CSV file not found: {csv_file}")
            return
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                filename = row.get('filename', '').strip()
                gdrive_url = row.get('gdrive_url', '').strip()
                
                if not filename or not gdrive_url:
                    print(f"⚠️  Skipping incomplete row: {row}")
                    continue
                
                sop_file = self.sop_directory / filename
                if not sop_file.exists():
                    print(f"❌ File not found: {filename}")
                    error_count += 1
                    continue
                
                success = self.create_metadata_file(sop_file, gdrive_url, overwrite=True)
                if success:
                    created_count += 1
                else:
                    skipped_count += 1
        
        print(f"\n📊 Batch processing complete!")
        print(f"   ✅ Created: {created_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")
        print(f"   ❌ Errors: {error_count}")
    
    def create_sample_csv(self, output_file: str = "sop_gdrive_mapping.csv") -> None:
        """
        Create a sample CSV file with all SOP files for manual editing
        """
        sop_files = self.find_sop_files()
        
        csv_path = Path(output_file)
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'gdrive_url'])
            
            for sop_file in sop_files:
                writer.writerow([sop_file.name, ''])
        
        print(f"📄 Created sample CSV: {output_file}")
        print(f"   Fill in the gdrive_url column and run: python generate_gdrive_metadata.py --csv {output_file}")
    
    def list_existing_metadata(self) -> None:
        """
        List all existing metadata files
        """
        metadata_files = list(self.sop_directory.glob("*.gdrive_metadata"))
        
        if not metadata_files:
            print("📭 No metadata files found")
            return
        
        print(f"📋 Found {len(metadata_files)} metadata files:")
        for metadata_file in sorted(metadata_files):
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                print(f"   ✅ {metadata_file.name.replace('.gdrive_metadata', '')}")
                print(f"      🔗 {data.get('gdrive_link', 'No link')}")
            except Exception as e:
                print(f"   ❌ {metadata_file.name} (Error: {e})")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Google Drive metadata for SOP documents")
    parser.add_argument("--directory", "-d", default="./documents", 
                       help="Directory containing SOP documents (default: ./documents)")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Interactive mode to map files to Google Drive URLs")
    parser.add_argument("--csv", "-c", 
                       help="Create metadata from CSV file (filename,gdrive_url)")
    parser.add_argument("--sample-csv", "-s", action="store_true",
                       help="Create a sample CSV file for batch processing")
    parser.add_argument("--list", "-l", action="store_true",
                       help="List existing metadata files")
    parser.add_argument("--overwrite", action="store_true",
                       help="Overwrite existing metadata files")
    
    args = parser.parse_args()
    
    generator = GDriveMetadataGenerator(args.directory)
    
    if args.sample_csv:
        generator.create_sample_csv()
    elif args.csv:
        generator.batch_mapping_from_csv(args.csv)
    elif args.list:
        generator.list_existing_metadata()
    elif args.interactive:
        generator.interactive_mapping()
    else:
        print("🔧 Google Drive Metadata Generator for SOPs")
        print("=" * 45)
        print()
        print("Usage options:")
        print("  --interactive     Interactive mapping mode")
        print("  --sample-csv      Create sample CSV for batch processing")
        print("  --csv FILE        Process CSV file with mappings")
        print("  --list            List existing metadata files")
        print()
        print("Example workflow:")
        print("  1. python generate_gdrive_metadata.py --sample-csv")
        print("  2. Edit sop_gdrive_mapping.csv with Google Drive URLs")
        print("  3. python generate_gdrive_metadata.py --csv sop_gdrive_mapping.csv")
        print()
        print("Or use interactive mode:")
        print("  python generate_gdrive_metadata.py --interactive")

if __name__ == "__main__":
    main()