#!/usr/bin/env python3
import sys
import os
import json
import urllib.request
import datetime
import argparse
import subprocess
import tempfile
import shutil
import traceback

# ==========================================
# 1. Spec template
# ==========================================
SPEC_TEMPLATE = """Name:           {crate_name}
Version:        {version}
Release:        1%{{?dist}}
Summary:        {summary}
License:        {license}
URL:            {url}
Source0:        {crate_name}-{version}-vendored.tar.gz

BuildRequires:  rust cargo

%description
{description}

%prep
%autosetup -n {crate_name}-{version}

%build
cargo build --release --offline

%install
rm -rf %{{buildroot}}
cargo install --root %{{buildroot}}%{{_prefix}} --path . --offline
rm -f %{{buildroot}}%{{_prefix}}/.crates.toml
rm -f %{{buildroot}}%{{_prefix}}/.crates2.json

%files
%{{_bindir}}/{crate_name}

%changelog
* {date} Auto Builder <auto@builder.local> - {version}-1
- Updated to {version}
"""

def fetch_crate_metadata(crate_name):
    url = f"https://crates.io/api/v1/crates/{crate_name}"
    req = urllib.request.Request(url, headers={'User-Agent': 'copr-rpm-builder/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))['crate']
    except Exception as e:
        print(f"Error: failed to read metadata")
        traceback.print_exc()
        sys.exit(1)

def prepare_offline_source(crate_name, version, dest_dir):
    """
    Download source -> Unzip -> Extract licenses -> Vendor dependencies -> Recompress
    """
    url = f"https://crates.io/api/v1/crates/{crate_name}/{version}/download"
    req = urllib.request.Request(url, headers={'User-Agent': 'copr-rpm-builder/1.0'})
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_tar = os.path.join(temp_dir, "original.tar.gz")
        source_folder_name = f"{crate_name}-{version}"
        source_dir = os.path.join(temp_dir, source_folder_name)
        
        print(f">> Downloading source: {url}")
        try:
            with urllib.request.urlopen(req) as response, open(original_tar, 'wb') as f:
                f.write(response.read())
        except Exception as e:
            print(f"Error: download failed")
            traceback.print_exc()
            sys.exit(1)
            
        subprocess.run(["tar", "-xzf", original_tar], cwd=temp_dir, check=True)

        print(">> Extracting metadata")
        env = os.environ.copy()
        env["CARGO_HOME"] = os.path.join(temp_dir, "cargo_home")
        
        license_str = "UNKNOWN"
        try:
            res = subprocess.run(
                ["cargo", "metadata", "--format-version", "1", "--manifest-path", "Cargo.toml"],
                cwd=source_dir, capture_output=True, text=True, env=env, check=True
            )
            licenses = set()
            for pkg in json.loads(res.stdout).get("packages", []):
                lic = pkg.get("license")
                if lic:
                    licenses.add(f"({lic})" if " OR " in lic or " AND " in lic else lic)
            if licenses:
                license_str = " AND ".join(sorted(list(licenses)))
                print(f">> >> License str collected: {license_str}")
        except Exception as e:
            print(f"Warning: license collection failed")
            traceback.print_exc()
            sys.exit(1)

        print(">> Vendoring dependencies")
        cargo_config_dir = os.path.join(source_dir, ".cargo")
        os.makedirs(cargo_config_dir, exist_ok=True)
        cargo_config_path = os.path.join(cargo_config_dir, "config.toml")
        
        try:
            res = subprocess.run(
                ["cargo", "vendor"], 
                cwd=source_dir, capture_output=True, text=True, env=env, check=True
            )
            with open(cargo_config_path, "w") as f:
                f.write(res.stdout)
        except Exception as e:
            print(f"Error: vendoring failed")
            traceback.print_exc()
            sys.exit(1)

        final_tarball_name = f"{crate_name}-{version}-vendored.tar.gz"
        final_tarball_path = os.path.join(dest_dir, final_tarball_name)
        print(f">> Re-compressingv {final_tarball_name}")
        subprocess.run(
            ["tar", "-czf", final_tarball_path, source_folder_name], 
            cwd=temp_dir, check=True
        )
        
        return final_tarball_name, license_str

def main():
    parser = argparse.ArgumentParser(description="Generate vendored source and spec for COPR.")
    parser.add_argument("crate_name", help="Name of the crate on crates.io")
    args = parser.parse_args()

    crate_name = args.crate_name
    cwd = os.getcwd()
    
    print(f"Collecting metadata {crate_name}")
    crate_data = fetch_crate_metadata(crate_name)
    version = crate_data.get('max_version', '0.0.0')
    description = crate_data.get('description', '') or f"Rust crate {crate_name}"
    summary = description.split('\n')[0].strip()[:67] + ("..." if len(description.split('\n')[0].strip()) > 67 else "")
    url = crate_data.get('repository') or crate_data.get('homepage') or f"https://crates.io/crates/{crate_name}"
    date = datetime.datetime.now().strftime("%a %b %d %Y")

    print("Preparing sources")
    tarball_name, license_str = prepare_offline_source(crate_name, version, cwd)
    if license_str == "UNKNOWN":
        license_str = crate_data.get('license', 'UNKNOWN')

    print("Generating spec file")
    spec_content = SPEC_TEMPLATE.format(
        crate_name=crate_name,
        version=version,
        summary=summary,
        description=description,
        license=license_str,
        url=url,
        date=date
    )
    
    spec_file_path = os.path.join(cwd, f"{crate_name}.spec")
    with open(spec_file_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"Spec created: {crate_name}.spec")
    print(f">> Tarball available at: {tarball_name}")

if __name__ == "__main__":
    main()
