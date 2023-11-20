# ----- CONFIGURE YOUR EDITOR TO USE 4 SPACES PER TAB ----- #
from io import DEFAULT_BUFFER_SIZE
import settings
import sys,os
sys.path.append(os.path.join(os.path.split(os.path.abspath(__file__))[0], 'lib'))
import lib.pymysql as db
import random

def connection():
    ''' User this function to create your connections '''
    con = db.connect(
        settings.mysql_host, 
        settings.mysql_user, 
        settings.mysql_passwd, 
        settings.mysql_schema)
    
    return con

def create_ngrams(text, num):
    text = text.replace("     ", " ")
    text = text.replace("    ", " ")
    text = text.replace("   ", " ")
    text = text.replace("  ", " ")
    
    mylist = text.split(" ")
   
    ln = len(mylist)
    lista = []
    for i in range(ln-(num-1)):
        if " " not in mylist[i:i+num]:
            lista.append(mylist[i:i+num])

    return lista

def mostcommonsymptoms(vax_name):
    
    stopwords=["this","the","no","a","an","is","and","at","or","not","to","of","on","for",
    "my","was","in","with","i","she","it","he","they","has","had","have", "that", "pm", "am", "by"]
    
    # Create a new connection
    con=connection()
    # Create a cursor on the connection
    cur=con.cursor()
    sql="""SELECT va.symptoms
            FROM vaccines v,vaccination va
            WHERE va.vaccines_vax_name=v.vax_name AND v.vax_name = '%s' ;""" % (vax_name)

    cur.execute(sql)
    # το κάνουμε λίστα από tuples 
    string=list(cur.fetchall())
    lstr=len(string)

    str = []
    list1 = []
    bigstr = ""
    for i in range(0,lstr-1):
        # κάνουμε το tuple string
        temp=string[i]
        str = temp[0]
        
        # αφαιρούμε τα σημεία στίξης
        punc = '''!()-[]{};:'", <>./?@#$%^&*~'''
        for ele in str:
            if ele in punc:
                str = str.replace(ele, " ")
        str=str.lower()
        symptoms=str.split()
        
        for j in symptoms:
            if j not in stopwords and j.isnumeric() == False :
                bigstr = bigstr + " " + j
                list1.append(j)

    list3 = create_ngrams(bigstr, 3)
    list2 = create_ngrams(bigstr, 2)
    
    counts3 = {}
    counts2 = {}
    counts1 = {}

    for x,y,z in list3:
        counts3[(x,y,z)] = counts3.get((x,y,z), 0 ) + 1

    for x,y in list2:
        counts2[(x,y)] = counts2.get((x,y), 0 ) + 1

    for x in list1:
        counts1[x] = counts1.get(x, 0) + 1

    lst1 = []
    for key, val in counts1.items():
        newtup = (val, key) 
        lst1.append(newtup)
    lst1 = sorted(lst1, reverse=True)
    
    lst2 = []
    for key, val in counts2.items():
        newtup = (val, key) 
        lst2.append(newtup)
    lst2 = sorted(lst2, reverse=True)
    
    lst3 = []
    for key, val in counts3.items():
        newtup = (val, key) 
        lst3.append(newtup)
    lst3 = sorted(lst3, reverse=True)

    return [("vax_name","result")] + lst1[:10] + lst2[:10] + lst3[:10]


def buildnewblock(blockfloor):
    
   # Create a new connection
    con=connection()

    # Create a cursor on the connection
    cur=con.cursor()

    if(int(blockfloor) > 7) :
        return[('result',), ('error',)]
    
    #ελέγχουμε αν υπάρχει η δυνατότητα να προσθέσουμε blockcode στον όροφο
    sql = """SELECT 1 AS answer WHERE EXISTS (SELECT * FROM block b, room r 
    WHERE '%s' = b.BlockFloor AND b.BlockCode < 9 )
    UNION
    SELECT 0 AS answer WHERE NOT EXISTS (SELECT * FROM block b, room r 
    WHERE '%s' = b.BlockFloor AND b.BlockCode < 9 )
    """ % (blockfloor, blockfloor)
    
    cur.execute(sql)
    results = cur.fetchone()
    print (results[0])

    if results[0] == 1 :
        # βρίσκουμε τις πτέρυγες στον όροφο 
        sql1 = """SELECT DISTINCT b.BlockCode FROM block b WHERE b.BlockFloor = '%s' """ % (blockfloor)
        cur.execute(sql1) 
        results1 = cur.fetchall()
        lista = list(results1)
        lng = len(lista)
        print ("length", lng)
        nos = []
        floor = int(blockfloor) 
        leng = lng
        
        for x in range(0, lng) : 
            nums = results1[x]
            nos.append(nums[0]) 
        j = 0
        for i in nos :
            if nos[j] == j + 1 :
                j = j+1
            else :    
                break
        if j < 9 :
            sql2 = """INSERT INTO block(BlockFloor, BlockCode) VALUES('%s', '%s') """ %(floor, (j+1))        
            try:
                cur.execute(sql2)
                
                n = random.randint(1,5)
                print("n -> ", n)
                for i in range(0, n):
                    rn = 1000*floor + 100*(j + 1) + i 
                    print ("would insert room ", rn)
                    sql3 = """INSERT INTO room(RoomNumber, RoomType, BlockFloor, BlockCode, Unavailable) VALUES('%s', 'quadruple', '%s', '%s', 0) """ %(rn, floor, (j+1))
                    cur.execute(sql3)
                    con.commit()
                
                return[('result',), ('ok',)]
            except:
                con.rollback()
                return[('result',), ('error',)] 
        else :
            return[('result',), ('error',)] 
        
def findnurse(x,y):

    # Create a new connection
    
    con=connection()
    
    # Create a cursor on the connection
    cur=con.cursor()
    sql = """SELECT n.Name, n.EmployeeID, COUNT(DISTINCT v.patient_SSN) AS number_of_patients 
        FROM patient p, vaccination v, nurse n, on_call o, appointment a
        WHERE p.SSN = v.patient_SSN AND v.nurse_EmployeeID = n.EmployeeID AND a.PrepNurse = n.EmployeeID AND o.Nurse = n.EmployeeID AND o.BlockFloor = '%s'
        GROUP BY a.PrepNurse, o.Nurse 
        HAVING COUNT(DISTINCT a.AppointmentID) >= '%s' AND COUNT(DISTINCT o.BlockCode) =  (SELECT COUNT(DISTINCT o.BlockCode) FROM  on_call o WHERE o.BlockFloor = '%s' ) ;""" % (x , y, x)
    try:
        cur.execute(sql)
        results = cur.fetchall()
       
    except:
        print ("Unable to find data")
    
    return [("Nurse", "ID", "Number of patients")] + list(results)

def patientreport(patientName):
    # Create a new connection
    con=connection()

    # Create a cursor on the connection
    cur=con.cursor()
    sql="""SELECT p.Name ,ph.Name AS physician ,n.Name AS nurse ,s.StayEnd AS discharge,t.Name AS treatment ,t.Cost AS treatment_cost  ,s.Room AS room ,r.BlockFloor AS floor ,r.BlockCode AS block
    FROM patient p,physician ph,nurse n,treatment t,undergoes u,stay s,room r
    WHERE u.Physician=ph.EmployeeID AND u.AssistingNurse=n.EmployeeID AND u.Treatment=t.Code AND u.Stay=s.StayID AND s.Room=r.RoomNumber AND p.Name=%s AND u.Patient=p.SSN
    GROUP BY p.Name;"""

    cur.execute(sql, patientName)
    results = cur.fetchall()

    return [("Patient","Physician", "Nurse", "Date of release", "Treatement going on", "Cost", "Room", "Floor", "Block"),]+ list(results)
   