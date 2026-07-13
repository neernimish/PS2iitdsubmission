from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import os

app=Flask(__name__)

def startupdb():
    mydb= sqlite3.connect('db.db')
    c=mydb.cursor()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS hospitals (
        hospital_id INTEGER PRIMARY KEY,
        hospital_name TEXT NOT NULL,
        hospital_locality TEXT NOT NULL,
        lat REAL,
        lon REAL
    );
    CREATE TABLE IF NOT EXISTS drugs (
        antibiotic_id INTEGER PRIMARY KEY,
        antibiotic_name TEXT NOT NULL,
        is_broaddrug INTEGER
    );
    CREATE TABLE IF NOT EXISTS patients (
        patient_id INTEGER PRIMARY KEY,
        patient_name TEXT NOT NULL,
        patient_age INTEGER NOT NULL,
        patient_gender TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS prescriptionswritten (
        prescription_id INTEGER PRIMARY KEY,
        hospital_id INTEGER NOT NULL,
        prescription_count INTEGER NOT NULL,
        patient_id INTEGER NOT NULL,
        init_drugid INTEGER NOT NULL,
        condition_diagnosed INTEGER NOT NULL,
        condition_pathogen TEXT,
        final_drugid INTEGER,
        FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id),
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    );
    ''')
    
    # Check if we need to insert dummy data
    c.execute("SELECT COUNT(*) FROM hospitals")
    if c.fetchone()[0] == 0:
        c.executescript("""
        INSERT INTO hospitals (hospital_name, hospital_locality, lat, lon) VALUES 
        ('AIIMS Delhi',            'Ansari Nagar',    28.5672, 77.1100),
        ('Safdarjung Hospital',    'Ansari Nagar',    28.5683, 77.2064),
        ('Max Super Speciality',   'Saket',           28.5273, 77.2122),
        ('Apollo Hospital',        'Sarita Vihar',    28.5367, 77.2831),
        ('Medanta The Medicity',   'Gurgaon',         28.4384, 77.0433),
        ('Fortis Escorts',         'Okhla',           28.5583, 77.2801),
        ('Sir Ganga Ram Hospital', 'Rajinder Nagar',  28.6385, 77.1895);
        """)
        
        c.executescript('''
        INSERT INTO drugs (antibiotic_name, is_broaddrug) VALUES 
        ('Amoxicillin', 1), 
        ('Azithromycin', 1), 
        ('Ciprofloxacin', 1), 
        ('Cephalexin', 1), 
        ('Doxycycline', 1), 
        ('Sulfamethoxazole/Trimethoprim', 1), 
        ('Clindamycin', 1),
        ('Levofloxacin', 1),
        ('Penicillin', 1),
        ('Vancomycin (MRSA)', 0),
        ('Linezolid (VRE, MRSA)', 0),
        ('Daptomycin (VRE, MRSA)', 0),
        ('Colistin (MDR Gram-negatives, Pseudomonas)', 0),
        ('Tigecycline (MDR Acinetobacter)', 0),
        ('Ceftazidime-avibactam (CRE)', 0),
        ('Meropenem-vaborbactam (CRE)', 0),
        ('Cefiderocol (MDR Gram-negatives)', 0),
        ('Fidaxomicin (C. difficile)', 0),
        ('Bedaquiline (MDR-TB)', 0),
        ('Delamanid (MDR-TB)', 0),
        ('Pretomanid (MDR-TB)', 0),
        ('Amikacin (MDR Gram-negatives)', 0),
        ('Polymyxin B (MDR Gram-negatives)', 0);
        ''')
    mydb.commit()
    mydb.close()

startupdb()

def hospitalgoodness(mydb):
    scorequery='''
    SELECT 
        h.hospital_id,
        d1.is_broaddrug AS start_type,
        d2.is_broaddrug AS end_type
    FROM prescriptionswritten p
    JOIN hospitals h ON p.hospital_id = h.hospital_id
    JOIN drugs d1 ON p.init_drugid = d1.antibiotic_id
    LEFT JOIN drugs d2 ON p.final_drugid = d2.antibiotic_id
    WHERE p.condition_diagnosed = 1
    '''
    df=pd.read_sql_query(scorequery, mydb)
    if df.empty:
        return {}
    
    def pointingtime(row):
        end_type=row['end_type']
        if pd.isna(end_type):
            end_type = row['start_type']
            
        if row['start_type']==1 and end_type==0:
            return 100
        elif row['start_type']==1 and end_type==1:
            return 0
        elif row['start_type']==0 and end_type==1:
            return 0
        elif row['start_type']==0 and end_type==0:
            return 100
        else:
            return 0
            
    df['perscriptionscore']= df.apply(pointingtime, axis=1)
    return df.groupby('hospital_id')['perscriptionscore'].mean().to_dict()

@app.route('/')
def index():
    mydb=                            sqlite3.connect("db.db")
    df=                              pd.read_sql_query("SELECT hospital_id, hospital_name, lat, lon FROM hospitals", mydb)
    scores=                          hospitalgoodness(mydb)
    mydb.close()
    
    df['score']=df['hospital_id'].map(scores).fillna(100)
    
    def get_color(score):
        if score >= 80:   
            return 'green'
        elif score >= 50: 
            return 'orange'
        else:             
            return 'red'
        
    df['color']=df['score'].apply(get_color)
    
    plt.figure(figsize=(10, 6))
    if not df.empty and 'lat' in df.columns and 'lon' in df.columns:
        for color, group in df.groupby('color'):
            plt.scatter(group['lon'], group['lat'], color=color, marker='o', s=100)
            
        plt.scatter([], [], color='green',  label='Green: 80-100 pts (Low AMR Risk)')
        plt.scatter([], [], color='orange', label='Orange: 50-79 pts (Medium AMR Risk)')
        plt.scatter([], [], color='red',    label='Red: <50 pts (High AMR Risk)')

        for i, row in df.iterrows():
            plt.text(row['lon'] + 0.005, row['lat'] + 0.005, row['hospital_name'], fontsize=9)
            
    plt.title('Delhi NCR Hospital Map & AMR Risk Rating')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.legend(loc='lower left',bbox_to_anchor=(1,0.5))
    plt.grid(True)
    plt.tight_layout()
    
    img=io.BytesIO()
    plt.savefig(img,format='png',bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    
    return render_template('index.html',plot_url=plot_url,hospitals=df.to_dict('records'))

@app.route('/register_patient',methods=['GET','POST'])
def register_patient():
    if request.method=='POST': 
        name=                         request.form['patient_name']
        age=                          request.form['patient_age']
        gender=                       request.form['patient_gender']
        mydb=                         sqlite3.connect('db.db')
        c=                            mydb.cursor()
        c.execute("INSERT INTO patients (patient_name, patient_age, patient_gender) VALUES (?, ?, ?)",(name,age,gender))
        mydb.commit()
        mydb.close()
        return redirect(url_for('submit_prescription'))
    return render_template('register_patient.html')

@app.route('/submit_prescription', methods=['GET', 'POST'])
def submit_prescription():
    mydb=                             sqlite3.connect("db.db")
    mydb.row_factory=                 sqlite3.Row
    c=                                mydb.cursor()
    
    if request.method=='POST':
        hospital_id=                  request.form['hospital_id']
        prescription_count=           request.form['prescription_count']
        patient_id=                   request.form['patient_id']
        init_drugid=                  request.form['init_drugid']
        condition_diagnosed=          request.form['condition_diagnosed']
        condition_pathogen=           request.form['condition_pathogen']
        final_drugid=                 request.form['final_drugid'] or None
        
        c.execute("""
        INSERT INTO prescriptionswritten (
            hospital_id, prescription_count,
            patient_id, init_drugid, condition_diagnosed, condition_pathogen, final_drugid
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,(hospital_id, prescription_count, patient_id, init_drugid, condition_diagnosed, condition_pathogen, final_drugid))
        mydb.commit()
        message=                     "Prescription submitted successfully!"
    else:
        message=None
        
    patients=                        c.execute("SELECT * FROM patients").fetchall()
    hospitals=                       c.execute("SELECT * FROM hospitals").fetchall()
    common_drugs=                    c.execute("SELECT * FROM drugs WHERE is_broaddrug = 1").fetchall()
    specialized_drugs=               c.execute("SELECT * FROM drugs WHERE is_broaddrug = 0").fetchall()
    mydb.close()
    
    return render_template('submit_prescription.html',patients=patients,hospitals=hospitals,common_drugs=common_drugs,specialized_drugs=specialized_drugs,message=message)

@app.route('/view_data')
def view_data():
    mydb = sqlite3.connect("db.db")
    mydb.row_factory = sqlite3.Row
    query = """
    SELECT 
        p.prescription_id,
        h.hospital_name,
        pt.patient_name,
        pt.patient_age,
        p.prescription_count,
        d1.antibiotic_name AS init_drug,
        p.condition_diagnosed,
        p.condition_pathogen,
        d2.antibiotic_name AS final_drug
    FROM prescriptionswritten p
    JOIN hospitals h ON p.hospital_id = h.hospital_id
    JOIN patients pt ON p.patient_id = pt.patient_id
    JOIN drugs d1 ON p.init_drugid = d1.antibiotic_id
    LEFT JOIN drugs d2 ON p.final_drugid = d2.antibiotic_id
    ORDER BY p.prescription_id DESC"""
    records=mydb.execute(query).fetchall()
    mydb.close()
    return render_template('view_data.html',records=records)

if __name__== "__main__":
    app.run(host='0.0.0.0',port=3000)
