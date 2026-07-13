import sqlite3
import random
##this is to generate sample data for the map, to show its functioning -- ONLY RUN ONCE PLS (if you run twice pls delete db.db and create it again and then run again only once)
mydb = sqlite3.connect('db.db')
cursor = mydb.cursor()


cursor.executescript('''
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


cursor.executescript('''
INSERT INTO hospitals (hospital_name, hospital_locality, lat, lon) VALUES 
('AIIMS Delhi',            'Ansari Nagar',    28.5672, 77.2100),
('Safdarjung Hospital',    'Ansari Nagar',    28.5683, 77.2064),
('Max Super Speciality',   'Saket',           28.5273, 77.2122),
('Apollo Hospital',        'Sarita Vihar',    28.5367, 77.2831),
('Medanta The Medicity',   'Gurgaon',         28.4384, 77.0433),
('Fortis Escorts',         'Okhla',           28.5583, 77.2801),
('Sir Ganga Ram Hospital', 'Rajinder Nagar',  28.6385, 77.1895);
''')


cursor.executescript('''
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

# Generate Dummy Patients
genders=['Male','Female']
for i in range(50):
    cursor.execute('INSERT INTO patients (patient_name, patient_age, patient_gender) VALUES (?, ?, ?)', (f'Patient {i+1}', random.randint(5, 80), random.choice(genders)))

# Generate Dummy Prescriptions
conditions= ['Urinary Tract Infection (E. coli)', 
             'Pneumonia (S. pneumoniae, K. pneumoniae)', 
             'Skin Infection (S. aureus, MRSA)', 
             'Throat Infection (Streptococcus pyogenes)', 
             'Tuberculosis (M. tuberculosis)', 
             'Sepsis (Various)', 
             'Other'
             ]

for i in range(200):
    hospital_id=            random.randint(1, 7)
    patient_id=             random.randint(1, 2147483647) #makes sure that the patient id is unique --i didnt want to code a unique check genuinely
    prescription_count=     random.randint(3, 14)
    init_drugid=            random.randint(1, 9)
    condition_diagnosed=    random.choices([1, 0], weights=[0.7, 0.3])[0]
    condition_pathogen=     random.choice(conditions) if condition_diagnosed else None
    
    if condition_diagnosed:
        final_drugid =      random.choices([random.randint(10, 23), random.randint(1, 9), None], weights=[0.5, 0.2, 0.3])[0]
    else:
        final_drugid =      random.choices([random.randint(10, 23), random.randint(1, 9), None], weights=[0.1, 0.4, 0.5])[0]
        
    cursor.execute('''
    INSERT INTO prescriptionswritten (
        hospital_id, prescription_count,
        patient_id, init_drugid, condition_diagnosed, condition_pathogen, final_drugid
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (hospital_id, prescription_count, patient_id, init_drugid, condition_diagnosed, condition_pathogen, final_drugid))

mydb.commit()
mydb.close()
