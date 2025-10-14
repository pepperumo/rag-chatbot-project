#!/usr/bin/env python3
"""
Dynamous Agent Deployment Configuration Script

This script helps configure custom domains for the Dynamous AI Agent system.
It copies the render.yaml_production template and replaces domain placeholders
with your actual custom domain.
"""

import os
import re
import shutil
import sys
from pathlib import Path


def validate_domain(domain):
    """Validate domain name format."""
    # Basic domain validation regex
    domain_pattern = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
    )
    
    if not domain_pattern.match(domain):
        return False
    
    # Check length
    if len(domain) > 253:
        return False
    
    # Check for valid TLD
    if '.' not in domain:
        return False
    
    return True


def get_domain_input():
    """Get and validate domain input from user."""
    print("🌐 Dynamous Agent Deployment - Domain Configuration")
    print("=" * 55)
    print()
    print("This script will configure your custom domains for the Dynamous AI Agent system.")
    print()
    print("Configuration options:")
    print("  1. Use root domain for frontend (e.g., myapp.com)")
    print("     Frontend: myapp.com + www.myapp.com")
    print("     API: api.myapp.com")
    print()
    print("  2. Use subdomain for frontend (e.g., chat.myapp.com)")
    print("     Frontend: chat.myapp.com")
    print("     API: api.myapp.com (or custom)")
    print()
    
    # Get frontend domain
    while True:
        frontend_domain = input("Enter your frontend domain (e.g., myapp.com or chat.myapp.com): ").strip().lower()
        
        if not frontend_domain:
            print("❌ Domain cannot be empty. Please try again.")
            continue
        
        # Remove protocol if provided
        frontend_domain = frontend_domain.replace('https://', '').replace('http://', '')
        
        # Remove trailing slash
        frontend_domain = frontend_domain.rstrip('/')
        
        if validate_domain(frontend_domain):
            break
        else:
            print(f"❌ Invalid domain format: {frontend_domain}")
            print("   Please enter a valid domain name (e.g., myapp.com, chat.example.org)")
    
    print()
    
    # Determine if it's a root domain or subdomain
    is_root_domain = len(frontend_domain.split('.')) <= 2
    
    if is_root_domain:
        # For root domains, suggest api.domain.com
        suggested_api = f"api.{frontend_domain}"
        print(f"✅ Root domain detected: {frontend_domain}")
        print(f"   Suggested API domain: {suggested_api}")
    else:
        # For subdomains, suggest api.rootdomain.com
        parts = frontend_domain.split('.')
        root_domain = '.'.join(parts[-2:])  # Get last two parts (domain.com)
        suggested_api = f"api.{root_domain}"
        print(f"✅ Subdomain detected: {frontend_domain}")
        print(f"   Suggested API domain: {suggested_api}")
    
    print()
    use_suggested = input(f"Use suggested API domain '{suggested_api}'? (Y/n): ").strip().lower()
    
    if use_suggested in ['', 'y', 'yes']:
        api_domain = suggested_api
    else:
        # Get custom API domain
        while True:
            api_domain = input("Enter your custom API domain (e.g., api.myapp.com): ").strip().lower()
            
            if not api_domain:
                print("❌ Domain cannot be empty. Please try again.")
                continue
            
            # Remove protocol if provided
            api_domain = api_domain.replace('https://', '').replace('http://', '')
            
            # Remove trailing slash
            api_domain = api_domain.rstrip('/')
            
            if validate_domain(api_domain):
                break
            else:
                print(f"❌ Invalid domain format: {api_domain}")
                print("   Please enter a valid domain name (e.g., api.myapp.com)")
    
    return frontend_domain, api_domain, is_root_domain


def copy_and_configure_template(frontend_domain, api_domain, is_root_domain):
    """Copy template and replace domain placeholders."""
    template_file = Path("render.yaml_production")
    output_file = Path("render.yaml")
    
    if not template_file.exists():
        print(f"❌ Template file {template_file} not found!")
        print("   Make sure you're running this script from the project root directory.")
        sys.exit(1)
    
    print(f"\n📄 Copying {template_file} to {output_file}...")
    
    # Read template content
    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace domain placeholders
    print(f"🔄 Configuring domains...")
    print(f"   Frontend: {frontend_domain}")
    print(f"   API: {api_domain}")
    
    # Replace frontend domain placeholders
    content = content.replace('YOUR_FRONTEND_DOMAIN', frontend_domain)
    content = content.replace('YOUR_API_DOMAIN', api_domain)
    
    # Handle www domain for root domains
    if is_root_domain:
        content = content.replace('YOUR_WWW_DOMAIN', f'www.{frontend_domain}')
    else:
        # For subdomains, remove the www line entirely
        lines = content.split('\n')
        filtered_lines = [line for line in lines if 'YOUR_WWW_DOMAIN' not in line]
        content = '\n'.join(filtered_lines)
    
    # Write configured file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Successfully created {output_file}")
    return output_file


def configure_blueprint_files(frontend_domain, api_domain):
    """Configure blueprint .env files from .env.example templates with domain placeholders."""
    blueprints_dir = Path("blueprints")
    
    if not blueprints_dir.exists():
        print(f"📝 Note: {blueprints_dir} directory not found, skipping blueprint configuration.")
        return
    
    blueprint_templates = [
        ("frontend-env.env.example", "frontend-env.env"),
        ("agent-api-env.env.example", "agent-api-env.env"), 
        ("rag-pipeline-env.env.example", "rag-pipeline-env.env")
    ]
    
    print(f"\n📄 Configuring blueprint environment files from templates...")
    
    for template_filename, output_filename in blueprint_templates:
        template_file = blueprints_dir / template_filename
        output_file = blueprints_dir / output_filename
        
        if not template_file.exists():
            print(f"⚠️  Template {template_file} not found, skipping...")
            continue
            
        print(f"🔄 Creating {output_file} from {template_file}...")
        
        # Read template content
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace domain placeholders
        content = content.replace('YOUR_FRONTEND_DOMAIN', frontend_domain)
        content = content.replace('YOUR_API_DOMAIN', api_domain)
        # Keep backwards compatibility
        content = content.replace('YOUR_CUSTOM_DOMAIN', frontend_domain)
        
        # Write configured file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"✅ Generated blueprint .env files")
    print(f"   Frontend domain: {frontend_domain}")
    print(f"   API domain: {api_domain}")


def print_dns_instructions(frontend_domain, api_domain, is_root_domain):
    """Print DNS configuration instructions."""
    print(f"\n🔧 DNS Configuration Instructions")
    print("=" * 50)
    print()
    print("To complete the setup, configure your DNS with these records:")
    print()
    
    if is_root_domain:
        print("📌 Frontend Domain Records (Root Domain Setup):")
        print(f"   Domain: {frontend_domain}")
        print(f"   Type: CNAME, Name: @, Target: dynamous-frontend.onrender.com")
        print(f"   Type: CNAME, Name: www, Target: dynamous-frontend.onrender.com")
        print()
        print("   💡 Note: Some DNS providers don't support CNAME for @ record.")
        print("   In that case, use A records with Render's IP addresses instead.")
        print()
    else:
        # Extract subdomain name for instructions
        subdomain = frontend_domain.split('.')[0]
        print("📌 Frontend Domain Records (Subdomain Setup):")
        print(f"   Domain: {frontend_domain}")
        print(f"   Type: CNAME, Name: {subdomain}, Target: dynamous-frontend.onrender.com")
        print()
    
    # API domain instructions
    api_subdomain = api_domain.split('.')[0]
    api_root = '.'.join(api_domain.split('.')[1:])
    print("📌 Agent API Domain Records:")
    print(f"   Domain: {api_domain}")
    print(f"   Type: CNAME, Name: {api_subdomain}, Target: dynamous-agent-api.onrender.com")
    print()
    
    print("⚠️  Important DNS Notes:")
    print("   • Remove any existing AAAA records (IPv6) for these domains")
    print("   • DNS propagation can take 5-60 minutes")
    print("   • If using Cloudflare:")
    print("     - Set SSL/TLS to 'Full' mode")
    print("     - Set proxy status to 'DNS Only' initially")
    print("     - After SSL certificates are issued, you can enable proxy")
    print()


def print_deployment_instructions():
    """Print next steps for deployment."""
    print("🚀 Next Steps - Deployment")
    print("=" * 30)
    print()
    print("1. Configure your DNS records (see instructions above)")
    print()
    print("2. Update environment variables in Render Dashboard:")
    print("   • Go to each service → Settings → Environment")
    print("   • Use the generated .env files in blueprints/ directory:")
    print("     - frontend-env.env for Frontend service")
    print("     - agent-api-env.env for Agent API service") 
    print("     - rag-pipeline-env.env for RAG Pipeline service")
    print("   • Copy-paste the environment variables from these files")
    print("   • Update placeholder values (API keys, database URLs, etc.)")
    print()
    print("3. Deploy to Render:")
    print("   • Push to your Git repository")
    print("   • Connect repository to Render")
    print("   • Use the generated render.yaml for deployment")
    print()
    print("4. Verify domains in Render Dashboard:")
    print("   • Go to Frontend Service → Settings → Custom Domains")
    print("   • Click 'Verify' next to your main domain")
    print("   • Go to Agent API Service → Settings → Custom Domains") 
    print("   • Click 'Verify' next to your api subdomain")
    print("   • Wait for TLS certificate issuance for both services")
    print()


def check_gitignore():
    """Check and update .gitignore if needed."""
    gitignore_path = Path(".gitignore")
    
    if not gitignore_path.exists():
        return
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing_items = []
    if 'render.yaml' not in content:
        missing_items.append('render.yaml')
    if 'blueprints/frontend-env.env' not in content:
        missing_items.append('blueprints/*.env files')
    
    if missing_items:
        print(f"\n📝 Note: Consider adding these to .gitignore:")
        for item in missing_items:
            print(f"   • {item}")
        print("   This prevents configured files from being committed to the repository.")


def main():
    """Main configuration script."""
    try:
        # Get domains from user
        frontend_domain, api_domain, is_root_domain = get_domain_input()
        
        # Copy template and configure
        output_file = copy_and_configure_template(frontend_domain, api_domain, is_root_domain)
        
        # Configure blueprint files
        configure_blueprint_files(frontend_domain, api_domain)
        
        # Print DNS instructions
        print_dns_instructions(frontend_domain, api_domain, is_root_domain)
        
        # Print deployment instructions
        print_deployment_instructions()
        
        # Check .gitignore
        check_gitignore()
        
        print("\n🎉 Configuration completed successfully!")
        print(f"   Your configured deployment file: {output_file}")
        print(f"   Your frontend domain: https://{frontend_domain}")
        print(f"   Your API domain: https://{api_domain}")
        
    except KeyboardInterrupt:
        print("\n\n❌ Configuration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during configuration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()