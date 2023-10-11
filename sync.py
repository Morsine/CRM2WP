from zeep import helpers
import re
import sys
from zeep import Client
from zeep.transports import Transport
from zeep import helpers
from lxml import etree
from zeep.plugins import HistoryPlugin
from zeep.helpers import serialize_object
import pyodbc 
import pandas as pd
from woocommerce import API
from json import dumps
from flask import Flask, request, Response
from waitress import serve
from time import sleep, perf_counter
import time
from threading import Thread
from datetime import datetime
import platform
import syncconfig as conf
debug = conf.debug
osname = platform.system()
print("############################################################################################")
print("#                                                                                          #")
print("#                 ░█████╗░██████╗░███╗░░░███╗██████╗░░██╗░░░░░░░██╗██████╗░                #")
print("#                 ██╔══██╗██╔══██╗████╗░████║╚════██╗░██║░░██╗░░██║██╔══██╗                #")
print("#                 ██║░░╚═╝██████╔╝██╔████╔██║░░███╔═╝░╚██╗████╗██╔╝██████╔╝                #")
print("#                 ██║░░██╗██╔══██╗██║╚██╔╝██║██╔══╝░░░░████╔═████║░██╔═══╝░                #")
print("#                 ╚█████╔╝██║░░██║██║░╚═╝░██║███████╗░░╚██╔╝░╚██╔╝░██║░░░░░                #")
print("#                 ░╚════╝░╚═╝░░╚═╝╚═╝░░░░░╚═╝╚══════╝░░░╚═╝░░░╚═╝░░╚═╝░░░░░                #")
print("#                                                                                          #")
print("#           Program is provides AS IS, with NO liability from the creator of it            #")
print("#                                                                                          #")
print("############################################################################################")

print("")
print(f"Platform: {osname}")
print(f"SQL Driver: {conf.sqldriver}")
print(f"Encryption: {conf.Encrypt}")
print(f"blind cert trust: {conf.TrustServerCertificate}")
print(f"Debug mode: {debug}")

app = Flask(__name__)
history = HistoryPlugin()   

conn = pyodbc.connect( f'Driver={conf.sqldriver};' #for windows hosts #for linux: /opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.3.so.1.1
                      f'Encrypt={conf.Encrypt};' #Disable encryption
                      f'TrustServerCertificate={conf.TrustServerCertificate};' #For *NIX hosts
                      f'Server={conf.DATABASE_SERVER}\{conf.DATABASE_INSTANCE};'
                      f'Database={conf.DATABASE_NAME};'
                      f'UID={conf.SQL_USERNAME};'
                      f'PWD={conf.SQL_PASSWORD};')
no_inventory = {
    'Message': None,
    'Success': True,
    'InventoryInfoList': None
}
wcapi = API(
    url=f"{conf.WPWCADDR}",
    consumer_key=f"{conf.WPWCKEY}",
    consumer_secret=f"{conf.WPWCSEC}",
    version=f"{conf.WPWCVER}",
    #verify_ssl="False", # !!!!!!!!!! WARNING !!!!! REMOVE IN PRODUCTION!!!!!!!!!! OR SET IT TO TRUE!!!!!!!!!!!!!!!
    timeout=30
)
ivalidinv = {
    'Message': None,
    'Success': True,
    'InventoryInfoList': None
}


# Initializing lines
syncqueueitems = []

runningsync = 0
def sku2id():
    global number
    global productid
    global dontupdate
    reqres = (wcapi.get(f"products/?sku={number}&").json())
    if debug == "yes":
         print(f"unmodified REQRES: {reqres}")
    reqres = dumps(reqres)
    reqres = [pair.replace('"', '').strip() and pair.replace(':', '=').strip() and pair.replace(' ', '').strip() and pair.replace('"', '').strip() for pair in reqres.split(',')]
    reqres = str(reqres)
    if debug == "yes":
         print(f"REQRES: {reqres}")
    if reqres == "['[]']":
         print("Product not found! creating it...")
         productspecsdetector()
         idfinder()
         createproduct()
         dontupdate = 1
    else:
        productid = re.search(r"id: (.*?)'", reqres).group(1)
        print(f"WC Produc ID: {productid}")
        dontupdate = 0
def updateproduct():
    global productid
    global s
    global makaninv
    global width
    updated_product_data = {
    "description": f"",
    "name": f"{s[0]}",
    "stock_quantity": f"{makaninv}", #only fetching Makan inventory, since this is the inventory direct sales rely on
    "price": "",
    "regular_price": f"{s[1]}",
    "sale_price": "",
    "manage_stock": True,
    "dimensions": {
      "width": f"{width}",
      "height": f"{thickness}"
    },
    "categories": [
    {
        "id": f"{catid}"
    }
    ],
    "tags": [
    {
        "id": f"{typeid}"
    },
    {
        "id": f"{qualityid}"
    }
    ],
    "attributes": [
    {
    "name": "برند",
    "position": 0,
    "visible": True,
    "variation": True,
    "options": [
        f"{prodbrand}"
    ]
    },
    {
    "name": "نوع ورق",
    "position": 0,
    "visible": True,
    "variation": True,
    "options": [
        f"{prodtype}"
    ]
    },
    {
    "name": "کیفیت",
    "position": 0,
    "visible": True,
    "variation": True,
    "options": [
        f"{prodquality}"
    ]
    },
    {
    "name": "هارد",
    "position": 0,
    "visible": True,
    "variation": True,
    "options": [
        f"{prodhard}"
    ]
    }
    ],
    

    }
    
    if debug == "yes":
         runres = wcapi.put(f'products/{productid}', updated_product_data).json()
         print(runres)
    if debug == "no":
         wcapi.put(f'products/{productid}', updated_product_data).json()
def createproduct():
    global productid
    global s
    global makaninv
    global itemno
    updated_product_data = {
    "description": f"",

    "name": f"{s[0]}",
    "stock_quantity": f"{makaninv}", #only fetching Makan inventory, since this is the inventory direct sales rely on
    "price": "",
    "sku": f"{number}",
    "regular_price": f"{s[1]}",
    "sale_price": "",
    "manage_stock": True,
    "dimensions": {
      "width": f"{width}",
      "height": f"{thickness}"
    },
    "categories": [
    {
        "id": f"{catid}"
    }
    ],
    "tags": [
    {
        "id": f"{typeid}"
    },
    {
        "id": f"{qualityid}"
    }
    ],
    "attributes": [
    {
    "name": "برند",
    "position": 0,
    "visible": True,
    "variation": True,
    "options": [
        f"{prodbrand}"
    ]
    },
    {
    "name": "نوع ورق",
    "position": 0,
    "visible": True,
    "variation": True,
    "options": [
        f"{prodtype}"
    ]
    },
    {
    "name": "کیفیت",
    "position": 0,
    "visible": True,
    "variation": True,
    "options": [
        f"{prodquality}"
    ]
    },
    {
    "name": "هارد",
    "position": 0,
    "visible": True,
    "variation": True,
    "options": [
        f"{prodhard}"
    ]
    }
    ],
    }
    wcapi.post(f'products', updated_product_data).json()

def Inventory():
        global x1result
        global number
        global invalidinventory
        global debug
        wsdl = "http://192.168.3.10/Services/API/IInventory.svc?wsdl"
        client = Client(wsdl, plugins=[history])
        request_data = {
            'userName': 'admin',
            'password': f'{conf.CRM_ADMIN_PASSWORD}',
            'productCode': f'{number}'
            ''
        }
        x1result = client.service.GetRemainingStock(**request_data)
        invalidinventory = "no"
        if debug == "yes":
            print(x1result)
        try: x1result = (x1result['InventoryInfoList']['InventoryInfo'])
        except TypeError:
             print("ERROR: Item has no assigned inventory!")
             #print(f"ERROR: Item has no assigned inventory!")
             invalidinventory = "yes"
             #exit()

def CDB():
    global number
    global history
    global s
    global conn
    cursor = conn.cursor()
    dbr = cursor.execute(f"SELECT Name, UnitPrice, LastPriceUpdate, SaleAble, BuyAble, Brand FROM Product WHERE Number = '{number}'")
    for i in cursor:
            s = i
def InventoryExtractor():
    global ieinput
    global inventory_id
    global inventory_stock
    global inventory_name
    ieinput = ieinput.replace("(", "")
    ieinput = ieinput.replace(")", "")
    inventory_id = re.search("'InventoryId': '(.*?)'", ieinput).group(1)
    inventory_name = re.search("'InventoryName': '(.*?)'", ieinput).group(1)
    inventory_stock = re.search("Decimal'(.*?)'", ieinput).group(1)
    inventory_stock = inventory_stock.replace(".00", "") #remove .00
    #return { f'id': {inventory_id}, 'stock': {inventory_stock} }
def InventoryDifferentiator():
    global inventory_realname
    global inventory_id
    global skipitem
    #print(inventory_id) #debug
    if inventory_id == "2a944817-a89c-4307-90a8-9449f6047ad8": #makan
         inventory_realname = "makan"
         skipitem = "no"
    else:
         inventory_realname = "UNKNOWN"
         skipitem = "yes"
         #exit()

def GetAllProducts():
    global prods
    global totalproducts
    global history
    global conn
    cursor = conn.cursor()
    dbr = cursor.execute("SELECT [Number]  FROM [PayamGostar2].[dbo].[Product] WHERE (ProductGroupId = '8AB2619B-4854-49FD-A9AF-F0626EFE900C' and Number > '0' and Name like '%*%')")
    columns = [column[0] for column in cursor.description]
    prods = [columns] + [row for row in cursor.fetchall()]
    totalproducts = len(prods)
    print(f"Total products: {totalproducts-1}")
    #item = [pair.replace(',', '').strip() and pair.replace('(', '').strip() and pair.replace(')', '').strip() for pair in item.split(',')]
    #print(allitems)

def crmprodidextractor():
    global prods
    global itemcount
    global itemno
    itemno = re.search(r"'(.*?)'", str(prods[itemcount])).group(1)
    print(f"Item {itemcount} is: {itemno}")
def logic():
    global s
    global number
    global ieinput
    global inventory_id
    global inventory_stock
    global inventory_name
    global inventory_realname
    global x1result
    global skipitem
    global factoryinv
    global makaninv
    global invalidinventory
    global debug
    
    CDB()
    if debug == "yes":
        print(s)
    try:
        s
    except NameError:
        s = None
    if s is None:
        #print("ERROR: Inavlid item or item not found")
        print("ERROR: Inavlid item or item not found")
    else:
        Inventory()
        if invalidinventory == "no":
            print(f"Item {number} found, trying to detect the inventory...")
            # initialization
            count = 0 #starting number
            skipitem = "yes" #assume invalid
            inventory_realname = "UNKNOWN" #assume invalid
            updated = "no" #assume invalid
            n = len(x1result) #max inventories
            while count in range(n):
                ieinput = str(x1result[count])
                InventoryExtractor()
                InventoryDifferentiator()
                if inventory_realname == "makan" and skipitem == "no": #searh for makan inventory
                    print(f"{inventory_realname}: {inventory_stock}")
                    makaninv = int(inventory_stock)
                    updated = "yes" #this item has been updated and there's no need to raise an error
                    break #break out of the loop!
                count += 1
            sku2id()
            if updated == "no":
                print("ERROR: INVENTORY DETECTION FAILED")
            if dontupdate == 1:
                print("New item. no need to run update code.")
            if dontupdate == 0 and updated != "no":
                print(f"Syncing item: {number}")
                productspecsdetector()
                idfinder()
                updateproduct()
        else:
            print("ERROR 02: Inavlid item or item not found")
        clearvars()

def clearvars():
    global s
    global number
    global productnumber
    s = None
    number = None
    productnumber = None


def updateall():
    global itemcount
    global totalproducts
    global number
    global runningsync
    runningsync = 1
    print("Updating all products")
    now = datetime.now()
    print("Task started at:", now)
    print("Fetching products list...")
    GetAllProducts() #receive a list of product numbers from MSSQL
    itemcount = 1 #skip first one since it's just junk xD (it should be 1)
    start_time = perf_counter()
    def updatecommand():
        global itemcount
        global totalproducts
        global number
        crmprodidextractor() #get product ID
        number = f"{itemno}" #pass var
        logic() #actual update code
    while itemcount in range(totalproducts):
        print("----------------------------------------------------------")
        #print(f"Syncing {itemcount} of {totalproducts-1} items") #what am I doing with my life?
        print(f"Syncing {itemcount} of {totalproducts-1} items") #what am I doing with my life? no, seriously..
        updatecommand()
        itemcount += 1
    end_time = perf_counter()
    print("----------------------------------------------------------")
    print(f"Update finished in {end_time- start_time: 0.2f} second(s).")
    #print(f'Update finished in {end_time- start_time: 0.2f} second(s).')
    print("----------------------------------------------------------")
    runningsync = 0
# webhook shit

def identifyrequest():
    global reqcat
    global fullurl
    fullurl = fullurl.replace("?", "'")
    reqcat = re.search(r"9000/(.*?)'", fullurl).group(1)
    print(f"Request type is: {reqcat}")

def identifyevent():
    global fullurl
    global eventtype
    eventtype = re.search(r"event=(.*?)&", fullurl).group(1)
    print(f"Event type is: {eventtype}")

def product2number():
    global fullurl
    global productnumber
    productnumber = re.search(r"productType=(.*?)&", fullurl).group(1)

def fetchid():
    global fullurl
    global itemcrmid
    itemcrmid = re.search(r"id=(.*?)&", fullurl).group(1)


def FindInvoiceById():
    global itemcrmid
    global productcrmid
    wsdl = "http://192.168.3.10/services/api/iinvoice.svc?wsdl"
    client = Client(wsdl, plugins=[history])
    request_data = {
        'userName': 'admin',
        'password': f'{conf.CRM_ADMIN_PASSWORD}',
        'invoiceId': f'{itemcrmid}'
        ''
    }
    x1result = client.service.FindInvoiceById(**request_data)
    x1result = str(x1result)
    productcrmid = re.search(r"'ProductId': '(.*?)'", x1result).group(1)
    print(f"product id is: {productcrmid}")

def FindProductById():
    global productcrmid
    global itemcrmid
    global conn
    global number
    cursor = conn.cursor()
    dbr = cursor.execute(f"SELECT [Number]  FROM [PayamGostar2].[dbo].[Product] WHERE Id = '{productcrmid}'")
    for i in cursor:
            s = i
    s = str(s)
    number = re.search(r"'(.*?)'", s).group(1)
    
def FindInventoryProduct():
    global conn
    global number
    global itemcrmid
    global productcrmid
    cursor = conn.cursor()
    dbr = cursor.execute(f"SELECT [ProductId] FROM [PayamGostar2].[dbo].[InventoryTransactionDetail] where InventoryTransactionId = '{itemcrmid}'")
    for i in cursor:
            s = i
    productcrmid = re.search(r"'(.*?)'", str(s)).group(1)

def produpdate():
    global runningsync
    global number
    global itemno
    global productnumber
    runningsync = 1
    product2number()
    print(f"Syncing item: {productnumber}")
    number = productnumber #pass var
    itemno = productnumber #pass var. don't judge me!
    logic() #sync!!
    print("done")
    print("----------------------------------------------------------")
    runningsync = 0
def invoiceupdate():
    global runningsync
    runningsync = 1
    fetchid()
    FindInvoiceById()
    FindProductById()
    logic() #sync!!
    print("done")
    print("----------------------------------------------------------")
    runningsync = 0

def inventoryupdate():
    global runningsync
    runningsync = 1
    fetchid()
    FindInventoryProduct()
    FindProductById()
    logic()
    print("done")
    print("----------------------------------------------------------")
    runningsync = 0

def syncqueue():
    global runningsync
    global syncqueueitems
    global reqcat
    global fullurl
    while True:
        if runningsync == 1:
            time.sleep(1) #wait till request is completed
        else:
            time.sleep(1) #wait for request
            if len(syncqueueitems) != 0:
                fullurl = syncqueueitems.pop(0)
                print(datetime.now(), file=sys.stderr)
                identifyrequest()
                syncdetectnrun()

def idfinder():
    #connect stuff with their IDs from woocommerce
    global catid
    global qualityid
    global typeid
    if prodbrand == "الماس":
         catid = "115"
    if prodbrand == "دشتستان":
         catid = "116"
    if prodbrand == "سمنان":
         catid = "117"
    if prodbrand == "تاراز":
         catid = "118"
    if prodbrand == "کاشان":
         catid = "119"
    if prodbrand == "مبارکه":
         catid = "120"
    if prodbrand == "شهریار":
         catid = "121"
    if prodbrand == "غرب":
         catid = "122"
    if prodbrand == "شهرکرد":
         catid = "123"
    if prodbrand == "چینی":
         catid = "124"
    if prodbrand == "روی اندود":
         catid = "125"  
    if prodquality == "A":
         qualityid = "126"
    if prodquality == "B":
         qualityid = "127"
    if prodquality == "AA":
         qualityid = "128"
    if prodquality == "AB":
         qualityid = "129"
    if prodtype == "گالوانیزه":
         typeid = "130"
    if prodtype == "گالوالوم":
         typeid = "131"
    if prodtype == "رنگی":
         typeid = "132"
    if prodtype == "روغنی":
         typeid = "133"
def productspecsdetector():
    global s
    global width
    global thickness
    global prodbrand
    global brandfound
    global prodquality
    global prodcolor
    global prodtype
    global prodhard

    #load product name and process it
    test = str({s[0]})
    if "{" or "}" or "'" in test:
        test = test.replace("{", "")
        test = test.replace("}", "")
        test = test.replace("'", "")
    if debug == "yes":
         print(f"Currently trying to detects details of {test}")
    if "رول" in test:
        test = test.replace("رول ", "")
    brands = [('الماس'), ('دشتستان'), ('سمنان'), ('تاراز'), ('کاشان'), ('مبارکه'), ('شهریار'), ('غرب'), ('شهرکرد'), ('چینی'), ('روی اندود')]
    rollqualities = [('AA'), ('AB'), ('A'), ('B')]
    rolltypes = [('روغنی'), ('رنگی'), ('گالوالوم')]
    rollcolors = [('سفید'), ('قرمز'), ('آبی'), ('زرد'), ('سبز'), ('نارنجی'), ('قهوه ای'), ('پرتغالی')]
    if debug == "yes":
         print(f"DEBUG MESSAGE B:{len(brands)}, Q:{len(rollqualities)}, T:{len(rolltypes)}, C:{len(rollcolors)}")
    all_words = test.split()
    #print(all_words[0])
    idk = all_words[0].split("*")
    print(f'width: {idk[0]}')
    width = {idk[0]}
    idk[1] = idk[1].replace("/", ".")
    print(f'thickness: {idk[1]}')
    thickness = {idk[1]}
    #check brand!
    #brands = list(brands)
    #reset var
    brandfound = 0
    prodquality = 0
    prodtype = 0
    while len(brands) != 0:
        if brands[0] in test:
                prodbrand = brands[0]
                brandfound = 1
                if debug == "yes":
                     print(f"DEBUG MESSAGE: Stopped at {len(brands)} with brand {prodbrand}")
                break
        else:
                brands.pop(0)
    if brandfound == 1:
        print(f"Brand is: {prodbrand}")
    if brandfound == 0:
        print("ERROR: BRAND NOT FOUND!!!")

    while len(rollqualities) != 0:
        if rollqualities[0] in test:
                prodquality = rollqualities[0]
                break
        else:
                rollqualities.pop(0)
                prodquality = "A"
    print(f"Quality is: {prodquality}")

    while len(rolltypes) != 0:
        if rolltypes[0] in test:
                prodtype = rolltypes[0]
                break
        else:
                rolltypes.pop(0)
                prodtype = "گالوانیزه"
    print(f"Type is: {prodtype}")

    if "hard" in test:
        prodhard = "بله"
    else:
        prodhard = "خیر"

    print(f"Product is hard: {prodhard}")

    while len(rollcolors) != 0:
        if rollcolors[0] in test:
                prodcolor = rollcolors[0]
                break
        else:
                rollcolors.pop(0)
                prodcolor = "no"
    print(f"Color is: {prodcolor}")


def syncdetectnrun(): #detect the god damn request and run it
    global runningsync
    global syncqueueitems
    global reqcat
    global fullurl
    if reqcat == "product":
        Thread(target = produpdate).start()
        return "<h1>Syncing product...</h1>"
    if reqcat == "syncall":
        Thread(target = updateall).start()
        return "<h1>Sync initiated! Please DO NOT request syncall till the current operation has completed!!!</h1> <h2>You can check the progress in the logs</h2>"
    if reqcat == "invoice":
        Thread(target = invoiceupdate).start()
        return "<h1>Syncing invoice...</h1>"
    if reqcat == "inventory":
        Thread(target = inventoryupdate).start()
        return "<h1>Syncing inventory...</h1>"
    return "Item added to sync queue"

@app.route('/product', methods = ['GET'])
@app.route('/invoice', methods = ['GET'])
@app.route('/inventory', methods = ['GET'])
@app.route('/syncall', methods = ['GET'])

def index():
    global fullurl
    global reqcat
    global eventtype
    global productnumber
    global itemcount
    global totalproducts
    global number
    global itemno
    global itemcrmid
    global productcrmid
    global syncqueueitems
    global reqcat
    global reqfullurl
    reqfullurl = request.url
    #identifyevent()
    syncqueueitems.append(reqfullurl)
    return "REQUEST RECEIVED!"
    

Thread(target = syncqueue).start() #start the queue

#app.run(host='0.0.0.0', port=9000)
serve(app, host="0.0.0.0", port=9000)
