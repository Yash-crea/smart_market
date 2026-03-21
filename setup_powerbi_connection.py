"""
Quick Power BI Setup Script for Django Grocery Store
Creates authentication and tests API connections
"""

import requests
import json
import pandas as pd
from datetime import datetime

class PowerBIConnector:
    """Helper class to test and configure Power BI connections"""
    
    def __init__(self, base_url="http://localhost:8000", username="admin", password="admin"):
        self.base_url = base_url
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        
        # Authenticate and get token
        self.authenticate(username, password)
    
    def authenticate(self, username, password):
        """Get authentication token for API access"""
        login_url = f"{self.base_url}/api/v1/auth/login/"
        
        try:
            response = requests.post(login_url, json={
                "username": username,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.headers['Authorization'] = f'Token {self.token}'
                print("✅ Authentication successful!")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(response.text)
                return False
                
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def test_api_endpoint(self, endpoint_path):
        """Test a specific API endpoint for Power BI connectivity"""
        url = f"{self.base_url}{endpoint_path}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint_path}")
                print(f"   Status: {response.status_code}")
                
                # Show data structure
                if isinstance(data, dict):
                    print(f"   Keys: {', '.join(data.keys())}")
                    for key, value in data.items():
                        if isinstance(value, list) and value:
                            print(f"   {key}: {len(value)} items")
                            if len(value) > 0 and isinstance(value[0], dict):
                                print(f"      Sample fields: {', '.join(list(value[0].keys())[:5])}")
                        elif isinstance(value, (int, float, str)):
                            print(f"   {key}: {value}")
                
                return True, data
            else:
                print(f"❌ {endpoint_path}")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                return False, None
                
        except requests.RequestException as e:
            print(f"❌ {endpoint_path}")
            print(f"   Connection error: {e}")
            return False, None
    
    def generate_powerbi_urls(self):
        """Generate the exact URLs for Power BI Web data sources"""
        print("\n🔗 POWER BI WEB DATA SOURCE URLs")
        print("=" * 60)
        print("Copy these URLs into Power BI 'Get Data' > 'Web':")
        print()
        
        endpoints = [
            "/api/v1/powerbi/demand-forecasts/",
            "/api/v1/powerbi/sales-analytics/", 
            "/api/v1/powerbi/inventory-alerts/",
            "/api/v1/powerbi/ml-predictions/generate/",
            "/api/v1/powerbi/ml-models/performance/",
            "/api/v1/recommendations/analytics/",
            "/api/v1/models/status/",
            "/api/v1/products/?format=json&limit=1000",
            "/api/v1/orders/?format=json&limit=1000"
        ]
        
        for endpoint in endpoints:
            # Add token as URL parameter for Power BI
            if '?' in endpoint:
                url = f"{self.base_url}{endpoint}&token={self.token}"
            else:
                url = f"{self.base_url}{endpoint}?token={self.token}"
            
            print(f"{url}")
        
        print(f"\n📝 Alternative: Use Authorization Header")
        print(f"Header Name: Authorization")
        print(f"Header Value: Token {self.token}")
    
    def test_all_powerbi_endpoints(self):
        """Test all Power BI-specific endpoints"""
        print("\n🧪 TESTING POWER BI ENDPOINTS")
        print("=" * 50)
        
        powerbi_endpoints = [
            "/api/v1/powerbi/demand-forecasts/",
            "/api/v1/powerbi/sales-analytics/",
            "/api/v1/powerbi/inventory-alerts/",
            "/api/v1/powerbi/ml-predictions/generate/",
            "/api/v1/powerbi/ml-models/performance/"
        ]
        
        results = {}
        for endpoint in powerbi_endpoints:
            success, data = self.test_api_endpoint(endpoint)
            results[endpoint] = {"success": success, "data": data}
            print()
        
        return results
    
    def create_sample_power_query(self, endpoint_path, sample_data):
        """Generate Power Query M code for specific endpoint"""
        
        if not sample_data or not isinstance(sample_data, dict):
            return None
        
        # Extract field names from sample data
        if 'data' in sample_data and sample_data['data']:
            fields = list(sample_data['data'][0].keys()) if sample_data['data'] else []
        elif 'forecasts' in sample_data and sample_data['forecasts']:
            fields = list(sample_data['forecasts'][0].keys()) if sample_data['forecasts'] else []
        elif 'results' in sample_data and sample_data['results']:
            fields = list(sample_data['results'][0].keys()) if sample_data['results'] else []
        else:
            fields = list(sample_data.keys())
        
        # Generate Power Query M code
        query_name = endpoint_path.replace("/", "_").replace("-", "_").strip("_")
        
        power_query = f'''
let
    // {query_name} Query for Power BI
    Source = Json.Document(Web.Contents("{self.base_url}{endpoint_path}?token={self.token}")),
    Data = Source[{"data" if "data" in sample_data else "results" if "results" in sample_data else "forecasts"}],
    ConvertedToTable = Table.FromList(Data, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    ExpandedRecords = Table.ExpandRecordColumn(ConvertedToTable, "Column1", 
        {{{", ".join([f'"{field}"' for field in fields[:10]])}}},
        {{{", ".join([f'"{field.replace("_", " ").title()}"' for field in fields[:10]])}}})
in
    ExpandedRecords
        '''
        
        return power_query.strip()
    
    def export_powerbi_config(self):
        """Export complete Power BI configuration"""
        print("\n📄 EXPORTING POWER BI CONFIGURATION")
        print("=" * 50)
        
        # Test all endpoints
        results = self.test_all_powerbi_endpoints()
        
        # Generate configuration file
        config = {
            "connection_info": {
                "base_url": self.base_url,
                "authentication": "Token-based",
                "token": self.token,
                "generated_at": datetime.now().isoformat()
            },
            "endpoints": {},
            "power_queries": {}
        }
        
        for endpoint, result in results.items():
            config["endpoints"][endpoint] = {
                "url": f"{self.base_url}{endpoint}?token={self.token}",
                "status": "working" if result["success"] else "error",
                "method": "GET",
                "headers": {"Authorization": f"Token {self.token}"}
            }
            
            if result["success"] and result["data"]:
                # Generate Power Query
                power_query = self.create_sample_power_query(endpoint, result["data"])
                if power_query:
                    config["power_queries"][endpoint] = power_query
        
        # Save to file
        with open("powerbi_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration saved to powerbi_config.json")
        
        # Create Power Query file
        with open("powerbi_queries.txt", "w") as f:
            f.write("POWER BI QUERIES FOR DJANGO GROCERY STORE\n")
            f.write("=" * 50 + "\n\n")
            
            for endpoint, query in config["power_queries"].items():
                f.write(f"// Query for {endpoint}\n")
                f.write(query)
                f.write("\n\n" + "-" * 40 + "\n\n")
        
        print("✅ Power Query code saved to powerbi_queries.txt")
        
        return config


def main():
    """Main function to set up Power BI connection"""
    print("🔌 POWER BI CONNECTION SETUP FOR DJANGO GROCERY STORE")
    print("=" * 70)
    
    # Get connection details
    base_url = input("Django server URL (default: http://localhost:8000): ").strip()
    if not base_url:
        base_url = "http://localhost:8000"
    
    username = input("Django username (default: admin): ").strip()
    if not username:
        username = "admin"
    
    password = input("Django password (default: admin): ").strip()
    if not password:
        password = "admin"
    
    print(f"\n🔗 Connecting to {base_url}...")
    
    # Initialize connector
    connector = PowerBIConnector(base_url, username, password)
    
    if connector.token:
        # Run comprehensive test
        config = connector.export_powerbi_config()
        
        # Generate URLs
        connector.generate_powerbi_urls()
        
        print(f"\n🎉 SETUP COMPLETE!")
        print(f"✅ Authentication token obtained")
        print(f"✅ API endpoints tested")
        print(f"✅ Power BI URLs generated")
        print(f"✅ Configuration files created")
        
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Open Power BI Desktop")
        print(f"2. Click 'Get Data' > 'Web'")
        print(f"3. Use URLs from powerbi_config.json")
        print(f"4. Or copy Power Query code from powerbi_queries.txt")
        print(f"5. Set up automatic refresh schedule")
        
        print(f"\n💡 TIP: For production, create a dedicated Power BI user in Django")
        print(f"     with read-only permissions for security.")
    
    else:
        print(f"\n❌ Setup failed. Please check:")
        print(f"• Django server is running")
        print(f"• Username/password are correct")
        print(f"• API endpoints are accessible")


if __name__ == '__main__':
    main()