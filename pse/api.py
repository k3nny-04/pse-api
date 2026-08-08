# Endpoint to search for companies by name or ticker symbol.
# Example usage: pass a query string like "Ayala" or "AC" to retrieve matching companies.
FND_CMPY_URL = "https://edge.pse.com.ph/autoComplete/searchCompanyNameSymbol.ax"

# Endpoint to retrieve detailed company information.
# Parameters required: cmpy_id (e.g., https://edge.pse.com.ph/companyInformation/form.do?cmpy_id=128)
CMPY_INFO_URL = "https://edge.pse.com.ph/companyInformation/form.do?"

# Endpoint to retrieve general stock data for a specific company.
# Parameters required: cmpy_id (e.g., https://edge.pse.com.ph/companyPage/stockData.do?cmpy_id=128)
STOCK_DATA_URL = "https://edge.pse.com.ph/companyPage/stockData.do?"

# Endpoint to fetch dividend and rights announcements.
# Payload required: {'cmpy_id': '128'}
STOCK_DIV_URL = "https://edge.pse.com.ph/companyPage/dividends_and_rights_list.ax?DividendsOrRights=Dividends"

# Endpoint to retrieve stock chart and tabular data within a specified date range.
# Payload format:
# {
#     "cmpy_id": "128",         # Company ID
#     "security_id": "108",     # Security ID
#     "startDate": "06-03-2024",# Start date in MM-DD-YYYY format
#     "endDate": "06-03-2025"   # End date in MM-DD-YYYY format
# }
STOCK_CHRT_TAB_DATA_URL = "https://edge.pse.com.ph/common/DisclosureCht.ax"

# Endpoint to retrieve dividend and rights information list.
# Parameters required: pageNum (page number), sortMode (e.g., "date")
# curl -X POST "https://edge.pse.com.ph/disclosureData/dividends_and_rights_info_list.ax?DividendsOrRights=Dividends" \
#   --data "pageNum=1&sortMode=date&dateSortType=DESC&cmpySortType=ASC"
DIV_LIST_URL = "https://edge.pse.com.ph/disclosureData/dividends_and_rights_info_list.ax?DividendsOrRights=Dividends"



