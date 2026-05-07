"""
50 domain QA questions on Middle East geopolitics — MMLU-style (4 choices, 1 correct).
Used by eval_qa.py to benchmark base vs CPT model.
"""

QUESTIONS = [
    # ── Iran nuclear (1-6) ────────────────────────────────────────────────────
    {
        "id": 1,
        "question": "The 2015 nuclear agreement between Iran and the P5+1 is known as:",
        "choices": {"A": "NPT Extension Agreement", "B": "Joint Comprehensive Plan of Action", "C": "Geneva Nuclear Protocol", "D": "Vienna Disarmament Accord"},
        "answer": "B",
    },
    {
        "id": 2,
        "question": "Iran's underground uranium enrichment facility that became a major point of contention in nuclear negotiations is located in:",
        "choices": {"A": "Bushehr", "B": "Isfahan", "C": "Fordow", "D": "Arak"},
        "answer": "C",
    },
    {
        "id": 3,
        "question": "Iran began enriching uranium to 20% at Fordow in 2012, prompting international concern because 20% enrichment is:",
        "choices": {"A": "weapons-grade by definition", "B": "a significant step toward the 90% needed for weapons", "C": "required for civilian power reactors", "D": "below the threshold monitored by the IAEA"},
        "answer": "B",
    },
    {
        "id": 4,
        "question": "The organization responsible for inspecting Iran's nuclear facilities under the NPT is:",
        "choices": {"A": "OPCW", "B": "NATO", "C": "UN Security Council", "D": "IAEA"},
        "answer": "D",
    },
    {
        "id": 5,
        "question": "Which US president withdrew the United States from the JCPOA in 2018?",
        "choices": {"A": "Barack Obama", "B": "George W. Bush", "C": "Donald Trump", "D": "Joe Biden"},
        "answer": "C",
    },
    {
        "id": 6,
        "question": "Iran's supreme leader who holds ultimate authority over the country's nuclear policy is:",
        "choices": {"A": "Hassan Rouhani", "B": "Ali Khamenei", "C": "Mahmoud Ahmadinejad", "D": "Ebrahim Raisi"},
        "answer": "B",
    },
    # ── Saudi Arabia (7-12) ───────────────────────────────────────────────────
    {
        "id": 7,
        "question": "Saudi Arabia's Vision 2030 economic diversification plan was launched under:",
        "choices": {"A": "King Abdullah", "B": "King Fahd", "C": "King Salman", "D": "Mohammed bin Salman"},
        "answer": "D",
    },
    {
        "id": 8,
        "question": "NEOM is a Saudi mega-project planned in which region of the kingdom?",
        "choices": {"A": "Asir province in the south", "B": "Tabuk province in the northwest", "C": "Eastern Province near Dhahran", "D": "Hejaz region near Mecca"},
        "answer": "B",
    },
    {
        "id": 9,
        "question": "Saudi Arabia is a founding member of which organization that coordinates oil production policy among major exporters?",
        "choices": {"A": "GCC", "B": "Arab League", "C": "OPEC", "D": "WTO"},
        "answer": "C",
    },
    {
        "id": 10,
        "question": "Saudi journalist Jamal Khashoggi was killed in 2018 inside the Saudi consulate in:",
        "choices": {"A": "Washington DC", "B": "London", "C": "Beirut", "D": "Istanbul"},
        "answer": "D",
    },
    {
        "id": 11,
        "question": "The 2017-2021 blockade of Qatar was led by Saudi Arabia alongside which other countries?",
        "choices": {"A": "UAE, Bahrain, and Egypt", "B": "UAE, Kuwait, and Oman", "C": "Jordan, Egypt, and Morocco", "D": "Iran, Turkey, and Sudan"},
        "answer": "A",
    },
    {
        "id": 12,
        "question": "Saudi Arabia's oil production is managed by the state company:",
        "choices": {"A": "Kuwait Petroleum", "B": "Abu Dhabi National Oil Company", "C": "Saudi Aramco", "D": "SABIC"},
        "answer": "C",
    },
    # ── Israel-Palestine (13-18) ──────────────────────────────────────────────
    {
        "id": 13,
        "question": "The Oslo Accords, which established the Palestinian Authority, were signed in:",
        "choices": {"A": "1979", "B": "1987", "C": "1993", "D": "2000"},
        "answer": "C",
    },
    {
        "id": 14,
        "question": "Hamas won Palestinian legislative elections in which year, prompting an international aid blockade of Gaza?",
        "choices": {"A": "2000", "B": "2003", "C": "2006", "D": "2009"},
        "answer": "C",
    },
    {
        "id": 15,
        "question": "The Abraham Accords (2020) normalized relations between Israel and which group of countries?",
        "choices": {"A": "Saudi Arabia and Qatar", "B": "UAE, Bahrain, Sudan, and Morocco", "C": "Egypt, Jordan, and Lebanon", "D": "Turkey, Oman, and Kuwait"},
        "answer": "B",
    },
    {
        "id": 16,
        "question": "The Palestinian Authority's headquarters are located in:",
        "choices": {"A": "Gaza City", "B": "East Jerusalem", "C": "Ramallah", "D": "Jericho"},
        "answer": "C",
    },
    {
        "id": 17,
        "question": "The Israeli separation barrier in the West Bank was primarily constructed during which decade?",
        "choices": {"A": "1980s", "B": "1990s", "C": "2000s", "D": "2010s"},
        "answer": "C",
    },
    {
        "id": 18,
        "question": "UN Security Council Resolution 242, passed after the 1967 war, called for:",
        "choices": {"A": "the establishment of a Palestinian state", "B": "Israeli withdrawal from occupied territories and recognition of all states in the region", "C": "an international military force in Jerusalem", "D": "sanctions against Israel"},
        "answer": "B",
    },
    # ── Turkey & Syria (19-23) ────────────────────────────────────────────────
    {
        "id": 19,
        "question": "Turkey's ruling party since 2002, led by Recep Tayyip Erdogan, is the:",
        "choices": {"A": "CHP", "B": "MHP", "C": "HDP", "D": "AKP"},
        "answer": "D",
    },
    {
        "id": 20,
        "question": "The Syrian civil war began following popular protests in:",
        "choices": {"A": "2009", "B": "2011", "C": "2013", "D": "2015"},
        "answer": "B",
    },
    {
        "id": 21,
        "question": "Syria's alleged use of chemical weapons in Ghouta in August 2013 crossed what US President Obama had called:",
        "choices": {"A": "a tripwire", "B": "a bright line", "C": "a red line", "D": "a line in the sand"},
        "answer": "C",
    },
    {
        "id": 22,
        "question": "Turkey's 2018 military operation targeting Kurdish YPG forces in northern Syria was called:",
        "choices": {"A": "Operation Euphrates Shield", "B": "Operation Olive Branch", "C": "Operation Peace Spring", "D": "Operation Northern Storm"},
        "answer": "B",
    },
    {
        "id": 23,
        "question": "The Kurdish militant group that Turkey designates as a terrorist organization, closely linked to Syrian YPG, is the:",
        "choices": {"A": "Peshmerga", "B": "Hezbollah", "C": "PKK", "D": "Hamas"},
        "answer": "C",
    },
    # ── Iraq (24-28) ──────────────────────────────────────────────────────────
    {
        "id": 24,
        "question": "The 2003 US invasion of Iraq was officially justified primarily by claims about:",
        "choices": {"A": "Al-Qaeda training camps", "B": "weapons of mass destruction", "C": "support for Palestinian groups", "D": "violations of the NPT"},
        "answer": "B",
    },
    {
        "id": 25,
        "question": "The US counterinsurgency 'surge' strategy in Iraq (2007) was led by General:",
        "choices": {"A": "Tommy Franks", "B": "Stanley McChrystal", "C": "David Petraeus", "D": "James Mattis"},
        "answer": "C",
    },
    {
        "id": 26,
        "question": "The Iraqi Kurdistan Region held an independence referendum in:",
        "choices": {"A": "2005", "B": "2014", "C": "2017", "D": "2019"},
        "answer": "C",
    },
    {
        "id": 27,
        "question": "The Shia cleric who led the Mahdi Army militia and later commanded the Saraya al-Salam in Iraq is:",
        "choices": {"A": "Ayatollah Sistani", "B": "Nouri al-Maliki", "C": "Muqtada al-Sadr", "D": "Ibrahim al-Jaafari"},
        "answer": "C",
    },
    {
        "id": 28,
        "question": "De-Baathification after the 2003 invasion of Iraq led to the dissolution of which institution, widely blamed for fueling the insurgency?",
        "choices": {"A": "the Iraqi parliament", "B": "the Iraqi army", "C": "the Iraqi central bank", "D": "the Iraqi intelligence services only"},
        "answer": "B",
    },
    # ── Lebanon & Hezbollah (29-33) ───────────────────────────────────────────
    {
        "id": 29,
        "question": "The Cedar Revolution in Lebanon was triggered by the 2005 assassination of Prime Minister:",
        "choices": {"A": "Fouad Siniora", "B": "Nabih Berri", "C": "Rafik Hariri", "D": "Michel Aoun"},
        "answer": "C",
    },
    {
        "id": 30,
        "question": "The 2006 Lebanon War was fought between Israel and:",
        "choices": {"A": "the Lebanese Armed Forces", "B": "Palestinian Islamic Jihad", "C": "the PLO", "D": "Hezbollah"},
        "answer": "D",
    },
    {
        "id": 31,
        "question": "Hezbollah's armed wing is primarily funded and equipped by:",
        "choices": {"A": "Qatar", "B": "Iran", "C": "Syria", "D": "Russia"},
        "answer": "B",
    },
    {
        "id": 32,
        "question": "The term 'Axis of Resistance' refers to the alliance between Iran, Syria, Hezbollah, and affiliated groups. This axis is opposed to:",
        "choices": {"A": "the Arab League", "B": "US influence and Israel", "C": "Russia and China", "D": "Sunni Gulf monarchies exclusively"},
        "answer": "B",
    },
    {
        "id": 33,
        "question": "The catastrophic explosion at the port of Beirut in August 2020 was caused by improperly stored:",
        "choices": {"A": "crude oil", "B": "liquefied natural gas", "C": "ammonium nitrate", "D": "military ammunition"},
        "answer": "C",
    },
    # ── Arab Spring (34-38) ───────────────────────────────────────────────────
    {
        "id": 34,
        "question": "The Arab Spring began when Mohamed Bouazizi set himself on fire in December 2010 in:",
        "choices": {"A": "Egypt", "B": "Libya", "C": "Bahrain", "D": "Tunisia"},
        "answer": "D",
    },
    {
        "id": 35,
        "question": "Egyptian president Hosni Mubarak resigned in February 2011 after how many years in power?",
        "choices": {"A": "15 years", "B": "20 years", "C": "30 years", "D": "40 years"},
        "answer": "C",
    },
    {
        "id": 36,
        "question": "Egypt's first democratically elected president Mohamed Morsi was affiliated with the:",
        "choices": {"A": "Salafi Nour Party", "B": "National Democratic Party", "C": "Muslim Brotherhood", "D": "Wafd Party"},
        "answer": "C",
    },
    {
        "id": 37,
        "question": "Libyan leader Muammar Gaddafi was captured and killed in:",
        "choices": {"A": "2010", "B": "2011", "C": "2012", "D": "2013"},
        "answer": "B",
    },
    {
        "id": 38,
        "question": "The Bahrain uprising of 2011 was primarily driven by:",
        "choices": {"A": "Sunni majority demanding democratic reform", "B": "Shia majority demanding political rights", "C": "labor unions demanding wage increases", "D": "youth movement protesting corruption"},
        "answer": "B",
    },
    # ── ISIS & terrorism (39-43) ──────────────────────────────────────────────
    {
        "id": 39,
        "question": "ISIS declared its caliphate in June 2014 from which mosque in Mosul?",
        "choices": {"A": "Al-Aqsa Mosque", "B": "Umayyad Mosque", "C": "Al-Nuri Mosque", "D": "Imam Ali Mosque"},
        "answer": "C",
    },
    {
        "id": 40,
        "question": "Al-Qaeda in the Arabian Peninsula (AQAP) operates primarily from:",
        "choices": {"A": "Saudi Arabia", "B": "Somalia", "C": "Yemen", "D": "Egypt"},
        "answer": "C",
    },
    {
        "id": 41,
        "question": "The Global Coalition against ISIS was formed in:",
        "choices": {"A": "2012", "B": "2013", "C": "2014", "D": "2016"},
        "answer": "C",
    },
    {
        "id": 42,
        "question": "ISIS leader Abu Bakr al-Baghdadi was killed in a US special forces raid in which country?",
        "choices": {"A": "Iraq", "B": "Syria", "C": "Turkey", "D": "Libya"},
        "answer": "B",
    },
    {
        "id": 43,
        "question": "The Quds Force is the external operations branch of which Iranian military organization?",
        "choices": {"A": "Iranian Army", "B": "Artesh", "C": "Iranian Navy", "D": "Islamic Revolutionary Guard Corps"},
        "answer": "D",
    },
    # ── Gulf states & diplomacy (44-47) ──────────────────────────────────────
    {
        "id": 44,
        "question": "The Gulf Cooperation Council (GCC) was founded in:",
        "choices": {"A": "1971", "B": "1981", "C": "1991", "D": "2001"},
        "answer": "B",
    },
    {
        "id": 45,
        "question": "Which Gulf state hosts the Al Udeid Air Base, the largest US military installation in the Middle East?",
        "choices": {"A": "Bahrain", "B": "UAE", "C": "Kuwait", "D": "Qatar"},
        "answer": "D",
    },
    {
        "id": 46,
        "question": "Yemen's civil war, which began in 2015, pits the Saudi-led coalition against:",
        "choices": {"A": "Al-Qaeda in the Arabian Peninsula", "B": "ISIS", "C": "Houthi rebels", "D": "the Southern Transitional Council"},
        "answer": "C",
    },
    {
        "id": 47,
        "question": "The Iran-Saudi Arabia diplomatic normalization agreement brokered by China was reached in:",
        "choices": {"A": "2021", "B": "2022", "C": "2023", "D": "2024"},
        "answer": "C",
    },
    # ── External powers (48-50) ───────────────────────────────────────────────
    {
        "id": 48,
        "question": "Russia's direct military intervention in the Syrian civil war began in:",
        "choices": {"A": "2013", "B": "2014", "C": "2015", "D": "2016"},
        "answer": "C",
    },
    {
        "id": 49,
        "question": "China's Belt and Road Initiative engagement in the Middle East has focused heavily on infrastructure investment in Egypt (Suez Canal zone) and:",
        "choices": {"A": "Saudi Arabia's oil pipelines", "B": "UAE port infrastructure", "C": "Turkish rail networks", "D": "Iraqi oil refineries"},
        "answer": "B",
    },
    {
        "id": 50,
        "question": "The two-state solution to the Israeli-Palestinian conflict refers to:",
        "choices": {"A": "Israel and Jordan sharing control of the West Bank", "B": "an independent Palestinian state coexisting alongside Israel", "C": "a confederation between Israel and Lebanon", "D": "shared sovereignty over Jerusalem under UN administration"},
        "answer": "B",
    },
]
