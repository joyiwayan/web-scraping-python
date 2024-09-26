import mysql.connector

# connect to DB
db = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="",
  database="data_pendamping_halal"
)
cursor = db.cursor()

# create table with province-level data
sql = """CREATE TABLE data_pph_province (
   id INT AUTO_INCREMENT PRIMARY KEY,
   province VARCHAR(255),
   email VARCHAR(255),
   name VARCHAR(255),
   no_telp VARCHAR(255),
   kabupaten VARCHAR(255),   -- Adding kabupaten (regency)
   kecamatan VARCHAR(255),   -- Adding kecamatan (sub-district)
   no_registrasi VARCHAR(20),  -- Adding no_registrasi (registration number)
   tgl_terbit DATE,   -- Adding tgl_terbit (issuance date)
   lembaga VARCHAR(255),  -- Adding lembaga (institution)
   pendampingan_pelaku_usaha TEXT -- Keeping the mentoring data
)"""
cursor.execute(sql)

print('Table data_pph_province created')
