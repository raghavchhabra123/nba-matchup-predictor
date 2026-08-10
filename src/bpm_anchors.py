"""Published 2025-26 Basketball-Reference BPM (Box Plus/Minus) by player.

BPM = points per 100 possessions above league average — a RAPM-informed
box-score metric (replacement level ≈ -2.0). These are the real published
values for ~120 rotation players (from basketball-reference.com advanced
table); the build script uses them directly and estimates only the deep bench.
For multi-team players the season total (2TM) row is used.
"""
BPM_ANCHORS = {
    'Nikola Jokic': 14.2, 'Nikola Jokić': 14.2,
    'Shai Gilgeous-Alexander': 11.7, 'Victor Wembanyama': 10.7,
    'Luka Doncic': 9.3, 'Luka Dončić': 9.3, 'Kawhi Leonard': 8.0,
    'Cade Cunningham': 6.3, 'Jimmy Butler': 5.5, 'Jimmy Butler III': 5.5,
    'Tyrese Maxey': 5.4, 'Stephen Curry': 5.4, 'Donovan Mitchell': 5.1,
    'Jalen Duren': 5.0, 'Joel Embiid': 4.9, 'LaMelo Ball': 4.7,
    'Kevin Durant': 4.5, 'Anthony Edwards': 4.5, 'Deni Avdija': 4.3,
    'Scottie Barnes': 4.2, 'Jalen Johnson': 4.2, 'Chet Holmgren': 4.2,
    'Alperen Sengun': 4.2, 'Alperen Şengün': 4.2, 'Jamal Murray': 4.1,
    'James Harden': 3.9, 'LeBron James': 3.5, 'Mitchell Robinson': 3.5,
    'Karl-Anthony Towns': 3.3, 'Jaylen Brown': 3.3, 'Derrick White': 3.2,
    'Jalen Brunson': 3.1, 'Ausar Thompson': 3.1, 'Evan Mobley': 3.0,
    'Donovan Clingan': 3.0, 'Josh Hart': 3.0, 'Michael Porter Jr.': 3.0,
    'Neemias Queta': 2.8, 'Kon Knueppel': 2.8, 'Austin Reaves': 2.8,
    'Mikal Bridges': 2.7, 'Reed Sheppard': 2.7, 'Jaylin Williams': 2.7,
    'Amen Thompson': 2.6, 'Jarrett Allen': 2.6, 'Lauri Markkanen': 2.6,
    'Collin Gillespie': 2.5, 'Isaiah Joe': 2.5, 'Trey Murphy III': 2.4,
    'Immanuel Quickley': 2.4, 'Payton Pritchard': 2.3, "De'Aaron Fox": 2.2,
    'Devin Booker': 2.2, 'Bam Adebayo': 2.0, 'OG Anunoby': 2.0,
    'Mark Williams': 2.0, 'Stephon Castle': 1.9, 'Ajay Mitchell': 1.9,
    'Jrue Holiday': 1.9, 'Brandon Miller': 1.6, 'Norman Powell': 1.6,
    'Julius Randle': 1.5, 'Cooper Flagg': 1.4, 'Paolo Banchero': 1.4,
    'Desmond Bane': 1.4, 'Dyson Daniels': 1.3, 'Tre Jones': 1.3,
    'Andrew Wiggins': 1.2, 'Nickeil Alexander-Walker': 1.2, 'Cason Wallace': 1.2,
    'Miles Bridges': 1.1, 'Rudy Gobert': 1.0, 'Ayo Dosunmu': 1.0,
    'Keldon Johnson': 0.9, 'Naz Reid': 0.9, 'Nic Claxton': 0.9,
    'Donte DiVincenzo': 0.8, 'Duncan Robinson': 0.8, 'Pascal Siakam': 0.7,
    'Onyeka Okongwu': 0.7, 'Daniel Gafford': 0.7, 'Sam Hauser': 0.6,
    'Saddiq Bey': 0.5, 'Brandon Ingram': 0.5, 'Devin Vassell': 0.5,
    'Jaime Jaquez Jr.': 0.1, 'Harrison Barnes': -0.1, 'DeMar DeRozan': -0.1,
    'Ivica Zubac': -0.3, 'CJ McCollum': -0.3, 'Jaden McDaniels': -0.3,
    'Cameron Johnson': -0.6, 'Wendell Carter Jr.': -0.6, 'Naji Marshall': -0.6,
    'Jaren Jackson Jr.': -0.6, 'Anthony Black': -0.6, 'Tristan da Silva': -0.6,
    'Jabari Smith Jr.': -0.7, 'Tim Hardaway Jr.': -0.7, 'Kris Dunn': -0.8,
    'Derik Queen': -0.8, 'Deandre Ayton': -0.9, 'Myles Turner': -0.9,
    'Davion Mitchell': -0.9, 'Aaron Wiggins': -0.9, 'Toumani Camara': -1.0,
    'Matas Buzelis': -1.0, 'Christian Braun': -1.2, 'Jake LaRavia': -1.2,
    'Peyton Watson': -1.2, 'Klay Thompson': -1.4, 'Max Christie': -1.5,
    'Zach LaVine': -1.5, 'Quentin Grimes': -1.6, 'P.J. Washington': -1.6,
    'Luguentz Dort': -2.0, 'Rui Hachimura': -2.2, 'Kyle Kuzma': -2.3,
    'Dillon Brooks': -2.3, 'Bruce Brown': -2.4, 'Zion Williamson': 2.9,
}
