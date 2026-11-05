# -*- coding: utf-8 -*-
"""
IMPD crosswalk builder — value sets (English value labels for harmonized variables).

Each value set is a list of (code, label_en). A value set is referenced by name from
variable_map.csv.  Codes are the HARMONIZED codes; where a survey uses different
codes, value_map.csv maps the survey code onto these.

Conventions
-----------
* Binary yes/no variables are harmonized to 1 = yes, 0 = no  ("yesno").
* Multiple-response "mentioned" items are 1 = mentioned, 0 = not mentioned ("mentioned").
* Agreement items keep the source direction 1 = strongly agree … 5 = strongly disagree.
* Where two surveys use incompatible detailed codings of the same concept, a "_det"
  value set keeps both codings side by side with the survey named in the label, and a
  "_cat" value set holds the harmonized coarse classes.
"""

VALUESETS = {}

def vs(name, pairs):
    assert name not in VALUESETS, name
    VALUESETS[name] = [(int(c) if float(c).is_integer() else c, l) for c, l in pairs]

# ---------------------------------------------------------------- generic scales
vs("yesno", [(0, "No"), (1, "Yes")])
vs("mentioned", [(0, "Not mentioned"), (1, "Mentioned")])
vs("agree5", [(1, "Strongly agree"), (2, "Agree"), (3, "Neither agree nor disagree"),
              (4, "Disagree"), (5, "Strongly disagree")])
vs("freq3", [(1, "Often/always"), (2, "Sometimes"), (3, "Never")])
vs("freq3_help", [(1, "Several times"), (2, "Once or a few times"), (3, "No")])
vs("freq3_nso", [(1, "Never"), (2, "Sometimes"), (3, "Often")])
vs("freq5_disc", [(1, "Never"), (2, "Almost never"), (3, "Occasionally"), (4, "Often"), (5, "Very often")])
vs("freq7_contact", [(1, "Never"), (2, "Once a year"), (3, "A few times a year"), (4, "At least monthly"),
                     (5, "At least weekly"), (6, "Several times a week"), (7, "Daily")])
vs("trait4", [(1, "Very"), (2, "A little"), (3, "Not"), (4, "Not at all")])
vs("good3", [(1, "Good"), (2, "Moderate"), (3, "Poor")])
vs("sex", [(1, "Male"), (2, "Female")])
vs("month", [(1, "January"), (2, "February"), (3, "March"), (4, "April"), (5, "May"), (6, "June"),
             (7, "July"), (8, "August"), (9, "September"), (10, "October"), (11, "November"), (12, "December")])
vs("who3", [(1, "Mainly the father"), (2, "Mainly the mother"), (3, "Both")])
vs("yes_no_sometimes", [(1, "Yes"), (2, "No"), (3, "Sometimes")])

# ---------------------------------------------------------------- survey / design
vs("survey", [(1, "SPVA 1988"), (2, "SPVA 1991"), (3, "SPVA 1994"), (4, "SPVA 1998"),
              (5, "SPVA 2002"), (6, "SPVN 2003 (SPVA refugee groups)"), (7, "LAS 2004/05"), (8, "SIM 2006"), (9, "SING 2009"),
              (10, "SIM 2011"), (11, "SIM 2015"), (12, "SIM 2020")])
vs("resptype", [(1, "Head of household - main questionnaire"),
                (2, "Other household member - mini questionnaire"),
                (3, "Household member - roster only, not interviewed"),
                (4, "Individually sampled respondent (person sample)")])
vs("proxy", [(1, "Person him/herself"), (2, "Other person (head of household)"), (3, "Other person"),
             (4, "Respondent unknown"), (8, "No mini questionnaire, cultural-integration module only (SPVA 2002)")])
vs("panel_first", [(1, "First in SPVA 2002"), (2, "First in SPVA 1998"), (3, "First in SPVA 1994"), (4, "First in SPVA 1991")])
vs("partner_avail", [(1, "Participates"), (2, "Not at home"), (3, "Refuses"), (4, "Other")])
vs("lang_interview", [(1, "Entirely Dutch"), (2, "Mostly Dutch"), (3, "Half Dutch, half other language"),
                      (4, "Mostly other language"), (5, "Entirely other language (own language)"),
                      (6, "English (SPVN 2003)"), (7, "French (SPVN 2003)"), (0, "Partner not interviewed (SPVA 2002)")])
vs("lang_questionnaire", [(1, "Dutch"), (2, "English"), (3, "Turkish"), (4, "Moroccan Arabic"), (5, "Polish"), (6, "Somali"), (7, "Farsi"), (8, "French")])

# ---------------------------------------------------------------- demography / household
vs("member_number", [(0, "Head of household"), (1, "Eldest child"), (2, "2nd child"), (3, "3rd child"), (4, "4th child"),
                     (5, "5th child"), (6, "6th child"), (7, "7th child"), (8, "8th child"), (9, "9th child"),
                     (10, "Partner"), (11, "Eldest other member"), (12, "2nd other member"), (13, "3rd other member"),
                     (14, "4th other member"), (15, "5th other member"), (16, "6th other member"),
                     (17, "7th other member"), (18, "8th other member")])
vs("pos_household", [(0, "Male head of household or partner"), (1, "Female head of household or partner"), (2, "Child"),
                     (3, "Sibling"), (4, "Parent or parent-in-law"), (5, "Grandparent"), (6, "Other relative"),
                     (7, "Friend"), (8, "Other")])
vs("pos_family", [(0, "Single man"), (1, "Single woman"), (2, "Member of a couple"), (3, "One of two parents"),
                  (4, "Lone father"), (5, "Lone mother"), (6, "Child (two parents)"), (7, "Child (one parent)"), (8, "Other"),
                  (9, "Child living with one or two parents (LAS 2004/05)"), (10, "Child living with other relatives (LAS 2004/05)")])
vs("hh_comp", [(1, "Single person"), (2, "Couple"), (3, "Parents with children"), (4, "Parents with children and others"),
                      (5, "Couple with others"), (6, "Father with children"), (7, "Mother with children"), (8, "Other"),
                      (9, "Child living with parents or relatives (LAS 2004/05)")])
vs("marstat", [(1, "Married"), (2, "Divorced"), (3, "Widowed"), (4, "Never married"), (5, "Cohabiting, unmarried (SPVN 2003)")])
vs("partner_status", [(0, "Single"), (1, "Married, partner in household"), (2, "Married, partner not in household"),
                      (3, "Cohabiting"), (4, "Partner, not cohabiting")])
vs("lat_partner", [(0, "No partner (single)"), (1, "Yes, partner living elsewhere"), (2, "No")])
vs("generation", [(0, "No migration background (native Dutch reference sample)"),
                  (1, "First generation (SPVA/SPVN: arrived aged 6 or older; SIM/CBS: born abroad)"),
                  (2, "Second generation (SPVA/SPVN: born in NL or arrived before age 6; SIM/CBS: born in NL, parent(s) born abroad)")])
vs("generation_prtnr", [(1, "First generation (partner born abroad; SPVA/SPVN: arrived aged 6 or older)"),
                        (2, "Second generation: partner born in the Netherlands (SPVA/SPVN: or arrived before age 6), native Dutch partners included")])
vs("ethgroup", [(1, "Turkish"), (2, "Moroccan"), (3, "Surinamese"), (4, "Antillean/Aruban"),
                (5, "Afghan"), (6, "Iraqi"), (7, "Iranian"), (8, "Former Yugoslav"), (9, "Somali"), (10, "Polish"), (11, "Chinese"),
                (90, "Native Dutch / third generation"), (95, "Other (non-target) origin group"), (99, "Migrant group unknown")])
vs("ethsubgroup", [(1, "Turks"), (2, "Kurds (Turkey)"), (3, "Armenians"), (4, "Moroccans (Arabic)"), (5, "Berbers"),
                   (6, "Hindustani Surinamese"), (7, "Creole Surinamese"), (8, "Javanese Surinamese"), (9, "Chinese Surinamese"),
                   (10, "Other Surinamese"), (11, "Antilleans"), (12, "Curacaoans"), (13, "Arubans"),
                   (20, "Does not identify with a subgroup (SPVN 2003)"), (21, "Pashtun/Pathan"), (22, "Tajik"), (23, "Hazara"),
                   (24, "Arab"), (25, "Kurd (Iraq/Iran)"), (26, "Persian"), (27, "Azerbaijani"), (29, "Bosniak"), (30, "Croat"),
                   (31, "Serb"), (32, "Montenegrin"), (33, "Slovene"), (34, "Macedonian"), (35, "Dir"), (36, "Darod"),
                   (37, "Isaaq"), (38, "Hawiye"), (39, "Rahanweyn"), (40, "Digil"), (41, "Dutch"), (98, "Other, specified in text")])
vs("partner_residence", [(1, "Netherlands"), (2, "Country of origin"), (3, "Elsewhere in Western Europe"),
                         (4, "Elsewhere in the world"), (5, "Whereabouts unknown"), (6, "Other country, unspecified (SIM)")])
vs("reunification_plan", [(1, "Yes, in progress"), (2, "No, not (yet) in progress"), (3, "No, not planning to"), (4, "Not possible")])
vs("origin_settlement", [(1, "Large city"), (2, "Small town"), (3, "Village"), (4, "Refugee camp"), (5, "Other")])

# ---------------------------------------------------------------- geography
vs("city4", [(1, "Amsterdam"), (2, "Rotterdam"), (3, "The Hague"), (4, "Utrecht"), (5, "Other survey municipality")])

# ---------------------------------------------------------------- migration / legal status
vs("mig_reason", [(1, "Work"), (2, "Study"), (3, "Social security (SPVA 2002)"), (4, "Political situation / war / conscription"),
                  (5, "Family reunification"), (6, "Marriage / family formation"), (7, "Came with family"),
                  (8, "Health / medical reasons"), (10, "Other"), (11, "Famine / poverty"),
                  (12, "Moved in with parents or partner already in NL (SIM)"), (13, "Future / education of children (SIM)"),
                  (14, "Came with parents (SIM)"), (15, "Came with partner (SIM)"), (16, "Moved in with partner already in NL (SIM partner)"),
                  (17, "Came on holiday and stayed (SIM 2006/2011)"),
                   (18, "Invited by the Dutch government (invited refugee; SING 2009)"), (19, "Religious persecution (SING 2009)")])
vs("reason_nl", [(1, "No real preference"), (2, "Partner lives in the Netherlands"), (3, "Compatriots in the Netherlands"),
                 (4, "Family or acquaintances already here"), (5, "Quality of health care"), (6, "Socio-economic situation"),
                 (7, "Political situation"), (8, "Asylum procedure / good reception"), (9, "Quality of education system"),
                 (10, "Travelled with a group going to the Netherlands"), (11, "Dutch always willing to help"), (12, "Other"),
                 (13, "For a job / work"), (14, "Safety"), (15, "Invitation by the Dutch government")])
vs("citizenship", [(1, "Dutch only"), (2, "Dual: Dutch and other"), (3, "Non-Dutch only"), (4, "Other / unspecified")])
vs("citizenship_det", [(1, "Dutch"), (11, "Dutch and Afghan"), (12, "Dutch and Iraqi"), (13, "Dutch and Iranian"),
                       (14, "Dutch and Yugoslav"), (15, "Dutch and Bosnian"), (16, "Dutch and Croatian"), (17, "Dutch and Serbian"),
                       (18, "Dutch and Montenegrin"), (19, "Dutch and Slovenian"), (20, "Dutch and Macedonian"), (21, "Dutch and Kosovar"),
                       (22, "Dutch and Kurdish"), (23, "Dutch and Somali"), (24, "Dutch and other nationality"),
                       (111, "Afghan"), (112, "Iraqi"), (113, "Iranian"), (114, "Yugoslav"), (115, "Bosnian"), (116, "Croatian"),
                       (117, "Serbian"), (118, "Montenegrin"), (119, "Slovenian"), (120, "Macedonian"), (121, "Kosovar"),
                       (122, "Kurdish"), (123, "Somali"), (124, "Other nationality")])
vs("permit_cat", [(1, "Permanent residence / settlement permit"), (2, "Refugee status (Convention) / asylum permit"),
                  (3, "Regular residence permit (temporary or unspecified)"), (4, "Conditional / temporary permit (VVTV, W-document)"),
                  (5, "Residence card for EU/EEA nationals"), (6, "No papers"), (7, "Other")])
vs("permit_det", [(101, "SPVA02: settlement permit (vestigingsvergunning)"), (102, "SPVA02: admission document (toelatingsbewijs)"),
                  (103, "SPVA02: residence permit"), (104, "SPVA02: stamp in passport"), (105, "SPVA02: temporary permit"),
                  (106, "SPVA02: no papers"), (107, "SPVA02: other"),
                  (201, "SPVN03: settlement permit (vestigingsvergunning)"), (202, "SPVN03: admitted as refugee (A-status)"),
                  (203, "SPVN03: residence permit, indefinite"), (204, "SPVN03: residence permit"),
                  (205, "SPVN03: residence card EU nationals"), (206, "SPVN03: conditional permit (VVTV)"), (207, "SPVN03: W-document"),
                  (208, "SPVN03: residence permit indefinite (new Aliens Act)"), (209, "SPVN03: residence permit indefinite, regular"),
                  (210, "SPVN03: residence permit temporary, asylum"), (211, "SPVN03: residence permit indefinite, asylum"),
                  (212, "SPVN03: residence card EU national (duplicate code)"), (213, "SPVN03: W-document (duplicate code)"), (214, "SPVN03: other")])

# ---------------------------------------------------------------- integration / language
vs("course_diploma", [(0, "No"), (1, "Yes, completed"), (2, "Still in progress (SPVN 2003)")])
vs("satisfied5", [(1, "Very satisfied"), (2, "Satisfied"), (3, "Neither satisfied nor dissatisfied"), (4, "Dissatisfied"), (5, "Very dissatisfied")])
vs("course_best", [(1, "Everything"), (2, "Language course"), (3, "Meeting other people"), (4, "Information on society / culture"),
                   (5, "Teachers / guidance / care"), (6, "Practical information about the Netherlands"), (7, "Computer lessons"),
                   (8, "Other"), (9, "Satisfied with nothing")])
vs("course_worst", [(1, "Too difficult / too fast"), (2, "Programme too short"), (3, "Guidance / teacher"), (4, "Language / course"),
                    (5, "Level too low"), (6, "Levels too different / groups too mixed"), (7, "Practical / government information"),
                    (8, "Dissatisfied with nothing"), (9, "Other")])
vs("reading4", [(1, "No, not at all"), (2, "No, with difficulty"), (3, "Yes, reasonably"), (4, "Yes, well")])
vs("other_language", [(0, "Dutch only"), (11, "Turkish"), (12, "Kurdish"), (21, "Moroccan Arabic"), (22, "Berber"),
                      (31, "Sranan Tongo"), (32, "Sarnami Hindi"), (33, "Javanese"), (34, "Chinese"), (35, "Papiamento"),
                      (36, "English"), (13, "Armenian"),
                      (41, "Dari (Afghan Persian)"), (42, "Pashto"), (43, "Turkic languages (Uzbek, Turkmen)"), (44, "Arabic (general)"), (45, "Sorani Kurdish"),
                      (46, "Turkmen"), (47, "Badini / Kurmanji Kurdish"), (48, "Farsi (Persian)"), (49, "Azeri"), (50, "Somali"), (51, "Polish"), (52, "Mandarin"),
                      (53, "Cantonese"), (54, "Wenzhounese"), (96, "Other")])

# ---------------------------------------------------------------- education
vs("edu_cntry", [(0, "No education"), (1, "Country of origin only"), (2, "Both origin country and Netherlands"), (3, "Netherlands only")])
vs("edu8", [(0, "None"), (1, "Primary (bao)"), (2, "Lower vocational (vbo/lbo)"), (3, "Lower general secondary (mavo)"),
            (4, "Upper vocational (mbo)"), (5, "Upper general secondary (havo/vwo)"), (6, "Higher professional (hbo)"), (7, "University (wo)")])
vs("edu_nl", [(-1, "No education at all"), (0, "Education abroad only"), (1, "Primary (bao)"), (2, "Lower vocational (vbo/lbo)"),
              (3, "Lower general secondary (mavo)"), (4, "Upper vocational (mbo)"), (5, "Upper general secondary (havo/vwo)"),
              (6, "Higher professional (hbo)"), (7, "University (wo)")])
vs("edu4", [(1, "At most primary"), (2, "Lower secondary (vbo/mavo)"), (3, "Upper secondary (mbo/havo/vwo)"), (4, "Tertiary (hbo/wo)")])
vs("edu5", [(0, "None"), (1, "At most primary"), (2, "Lower secondary (vbo/mavo)"), (3, "Upper secondary (mbo/havo/vwo)"), (4, "Tertiary (hbo/wo)")])
vs("edu_abroad_det", [(0, "Primary, 4 years or less"), (1, "Primary, 5 years or more"),
                      (2, "SPVA02: lower vocational (vbo)"), (3, "SPVA02: lower general secondary (mavo)"), (4, "SPVA02: upper vocational (mbo)"),
                      (5, "SPVA02: upper general secondary (havo/vwo)"), (6, "SPVA02: higher professional (hbo)"), (7, "SPVA02: university (wo)"),
                      (12, "SPVN03: lower secondary"), (13, "SPVN03: upper secondary"), (14, "SPVN03: higher education")])
vs("edu_parent_det", [(0, "None"), (1, "Primary"),
                      (2, "SPVA02: lower vocational (vbo)"), (3, "SPVA02: lower general secondary (mavo)"), (4, "SPVA02: upper vocational (mbo)"),
                      (5, "SPVA02: upper general secondary (havo/vwo)"), (6, "SPVA02: higher professional (hbo)"), (7, "SPVA02: university (wo)"),
                      (12, "SPVN03: lower secondary"), (13, "SPVN03: upper secondary"), (14, "SPVN03: higher education")])
vs("edu_current", [(0, "Bridge class (brugklas) (SPVA 2002)"), (1, "Primary (bao)"), (2, "Lower vocational (vbo/lbo)"),
                   (3, "Lower general secondary (mavo)"), (4, "Upper vocational (mbo)"), (5, "Upper general secondary (havo/vwo)"),
                   (6, "Higher professional (hbo)"), (7, "University (wo)")])
vs("edu7", [(1, "Primary (bao)"), (2, "Lower vocational (vbo/lbo)"), (3, "Lower general secondary (mavo)"), (4, "Upper vocational (mbo)"),
            (5, "Upper general secondary (havo/vwo)"), (6, "Higher professional (hbo)"), (7, "University (wo)")])
vs("edu_type", [(0, "No education"), (1, "Full-time day education"), (2, "Part-time day education"), (3, "Evening education"),
                (4, "Practical / apprenticeship"), (5, "Other")])
vs("participation", [(0, "No"), (1, "Full-time")])
vs("bridge_class", [(1, "vmbo"), (2, "vmbo/havo/vwo"), (3, "vmbo/havo"), (4, "havo/vwo"), (5, "Other")])
vs("field_cat", [(1, "General"), (2, "Economic / administrative"), (3, "Technical"), (4, "Care / health / services"), (5, "Other")])
vs("field_det", [(1, "SPVA02: general"), (2, "SPVA02: economic-administrative"), (3, "SPVA02: technical"), (4, "SPVA02: care"), (5, "SPVA02: other"),
                 (11, "SPVN03: general education"), (12, "SPVN03: languages, arts, philosophy"), (13, "SPVN03: agricultural"),
                 (14, "SPVN03: technical, natural sciences"), (15, "SPVN03: economic, administrative, legal"), (16, "SPVN03: medical, paramedical"),
                 (17, "SPVN03: socio-cultural"), (18, "SPVN03: personal and social care"), (19, "SPVN03: teacher training"), (20, "SPVN03: other")])
vs("dropout", [(0, "Diploma Dutch secondary education"), (1, "Dropout from Dutch secondary education")])
vs("diploma_eval", [(1, "Yes, had it evaluated"), (0, "No"), (2, "Evaluation in progress")])
vs("diploma_eval_result", [(1, "Rated higher than in country of award"), (2, "Rated equal"), (3, "Rated lower"), (4, "Not recognised in the Netherlands")])

# ---------------------------------------------------------------- labour market
vs("lab_rel", [(1, "Working 12 hours or more"), (2, "Wants work, searching, available, registered"), (3, "Wants work, searching, available"),
                    (4, "Wants work, searching, registered"), (5, "Wants work, registered"), (6, "Benefit only"),
                    (7, "Other, wants work"), (8, "Other, not in labour force")])
vs("in_lf", [(0, "Not in labour force"), (1, "In labour force")])
vs("reg_unemp", [(0, "Other labour force"), (1, "Registered unemployed")])
vs("not_working", [(0, "Other labour force"), (1, "Not working")])
vs("main_activity", [(0, "Working 12 hours or more"), (1, "Unemployed / job seeking"), (2, "Homemaker"), (3, "Work-disabled"),
                     (4, "Pupil / student"), (5, "Retired / state pension"), (6, "Other"), (7, "No legal status (SPVN 2003)")])
vs("skill_level", [(1, "Elementary"), (2, "Lower"), (3, "Intermediate"), (4, "Higher"), (5, "Scientific")])
vs("industry9", [(0, "Agriculture, fishing, mining"), (1, "Manufacturing"), (2, "Construction"), (3, "Repair, trade, hotels and catering"),
                 (4, "Transport, storage, communication"), (5, "Financial and business services"), (6, "Public administration, education"),
                 (7, "Health and welfare"), (8, "Culture and other services")])
vs("employment_type", [(1, "Employee"), (2, "Self-employed / own business"), (3, "Freelance")])
vs("prev_status", [(1, "Paid work 12 hours or more per week"), (2, "Paid work less than 12 hours"), (3, "No paid work")])
vs("job_level_vs_prev", [(1, "Current higher"), (2, "Same"), (3, "Current lower")])
vs("reason_job_change", [(1, "Did not like the work"), (2, "Did not like colleagues"), (3, "To get promoted"), (4, "Work too far away"),
                         (5, "Wage too low"), (6, "Moved house"), (7, "Work ended"), (8, "Other")])
vs("sector", [(1, "Government"), (2, "Non-profit"), (3, "Private company")])
vs("job_found", [(1, "Family / friends"), (2, "Employment office"), (3, "Temp agency"), (4, "Enquiring"), (5, "School / internship"),
                 (6, "Subsidised job scheme"), (7, "Advertisement"), (8, "Internet"), (9, "Was asked"), (10, "Other"),
                 (11, "Via refugee organisation (SPVN 2003)"), (12, "Via placement agency (SPVN 2003)")])
vs("promotion_barrier", [(1, "Education too low"), (2, "Too little experience"), (3, "Works part-time / side job"), (4, "Prejudice"),
                         (5, "No internal vacancies"), (6, "No interest"), (7, "Language problems"), (8, "Already in highest position"), (9, "Too old (SIM 2006)"), (10, "Other")])
vs("reason_other_job", [(1, "Does not like the work"), (2, "Does not like colleagues"), (3, "To get promoted"), (4, "Too far away"),
                        (5, "Wage too low"), (6, "Moving house"), (7, "Other")])
vs("contract_perm", [(1, "Permanent"), (2, "Temporary")])
vs("contract_type", [(0, "Permanent appointment"), (1, "Fixed-term contract"), (2, "Temporary, prospect of permanent"), (3, "Temp agency work"),
                     (4, "On-call / stand-in"), (5, "Min-max contract"), (6, "Zero-hours contract"), (7, "Probation period"),
                     (8, "Subsidised job scheme (ID-banen)"), (9, "Other")])
vs("hours12", [(1, "Less than 12 hours"), (2, "12 hours or more")])
vs("employee_ethnicity", [(1, "Own group"), (2, "Mixed"), (3, "Native Dutch")])
vs("prior_status_selfemp", [(1, "Unemployed / job seeking"), (2, "Homemaker"), (3, "Work-disabled"), (4, "Student"), (5, "Other")])
vs("how_left", [(1, "Dismissed by employer"), (2, "Resigned"), (3, "Became work-disabled"), (4, "Retired / early retirement")])
vs("reason_dismissal", [(1, "Reorganisation / downsizing"), (2, "Company bankrupt"), (3, "End of temporary contract"), (4, "Health"),
                        (5, "Became work-disabled"), (6, "Conflict"), (7, "Returned to school"), (8, "Did not like the work"),
                        (9, "Private reasons"), (10, "Other"), (11, "Poor performance (SIM 2011)")])
vs("last_visit", [(1, "Less than 1 month ago"), (2, "1-6 months ago"), (3, "6-12 months ago"), (4, "A year or more ago")])
vs("wants_work", [(1, "Yes, 12 hours or more per week"), (2, "Yes, less than 12 hours per week"), (3, "Does not want work")])
vs("not_available_reason", [(1, "Finishing studies"), (2, "Arranging childcare"), (3, "Finishing voluntary work"), (4, "Notice period current job"), (5, "Other")])
vs("reason_not_seeking", [(1, "Health / work disability"), (2, "Satisfied with current job of <12 hours"), (3, "Studying / at school"),
                          (4, "Housework"), (5, "Too old"), (6, "No work available / cannot find work"), (7, "No time / did not get round to it"),
                          (8, "Would not be hired anyway"), (9, "Other activities / no need"), (10, "Other"),
                          (11, "Wants to study first (SPVN 2003)"), (12, "Returning to origin country soon (SPVN 2003)"),
                          (13, "Insufficient language skills (SPVN 2003)"), (14, "No legal status (SPVN 2003)")])
vs("job_match", [(1, "Yes, job matches education"), (2, "No, over-educated"), (3, "No, under-educated"), (4, "Educated for something else")])
vs("future5", [(1, "In paid employment"), (2, "Unemployed"), (3, "Work-disabled"), (4, "Retired"), (5, "Working in the household"),
               (6, "Not living in the Netherlands")])

# ---------------------------------------------------------------- income
vs("income_cat10", [(1, "Less than 550 euro"), (2, "550-750 euro"), (3, "750-950 euro"), (4, "950-1150 euro"), (5, "1150-1350 euro"),
                    (6, "1350-1550 euro"), (7, "1550-1750 euro"), (8, "1750-2000 euro"), (9, "2000-2250 euro"), (10, "2250 euro or more")])
vs("income_cat8", [(1, "Less than 750 euro"), (2, "750-950 euro"), (3, "950-1150 euro"), (4, "1150-1350 euro"), (5, "1350-1550 euro"),
                   (6, "1550-1750 euro"), (7, "1750-2000 euro"), (8, "2000 euro or more")])
vs("income_cat9", [(1, "Less than 750 euro"), (2, "750-950 euro"), (3, "950-1150 euro"), (4, "1150-1350 euro"), (5, "1350-1550 euro"),
                   (6, "1550-1750 euro"), (7, "1750-2000 euro"), (8, "2000-2250 euro"), (9, "2250 euro or more")])
vs("benefit_type", [(1, "Social assistance (bijstand)"), (2, "Unemployment benefit (WW)"), (3, "Disability benefit (WAO)"),
                    (4, "Pension / state pension (AOW) / early retirement"), (5, "Student grant / UAF"), (6, "Other")])
vs("money_worries", [(1, "Almost constantly"), (2, "Very often"), (3, "Occasionally"), (4, "Never")])
vs("support_who", [(1, "Nobody"), (2, "Partner only"), (3, "Children (and partner)"), (4, "Parents only"), (5, "Others only"),
                   (6, "Other family only (SPVN 2003)")])

# ---------------------------------------------------------------- housing
vs("move_reason", [(1, "Larger or better dwelling"), (2, "Bought a house"), (3, "Cheaper dwelling"), (4, "Disliked neighbourhood"),
                   (5, "Work / better job chances"), (6, "Education"), (7, "Contacts with compatriots etc."), (8, "Medical reasons"), (9, "Other")])
vs("nbhd_pleasant4", [(1, "Pleasant"), (2, "So-so"), (3, "Not pleasant"), (4, "Not at all pleasant")])
vs("nbhd_pleasant5", [(1, "Very pleasant"), (2, "Pleasant"), (3, "Neither pleasant nor unpleasant"), (4, "Not pleasant"), (5, "Not at all pleasant")])
vs("nbhd_foreigners", [(1, "Too many foreigners"), (2, "Fine"), (3, "Too few foreigners")])
vs("nbhd_dutch", [(1, "Too few Dutch"), (2, "Fine"), (3, "Too many Dutch")])
vs("move_destination", [(1, "Same municipality"), (2, "Amsterdam / Rotterdam / The Hague / Utrecht"), (3, "Another municipality")])

# ---------------------------------------------------------------- health / social
vs("health5", [(1, "Excellent"), (2, "Good"), (3, "Fair"), (4, "Poor"), (5, "Very poor")])
vs("member_type", [(1, "Sports club"), (2, "Trade union"), (3, "Organisation with a social goal"), (4, "Hobby club"),
                   (5, "Education / school association"), (6, "Political party"), (7, "Social club"), (8, "Ethnic / cultural association"), (9, "Other")])
vs("ethnic_share", [(1, "Many from own group"), (2, "Few"), (3, "(Almost) none")])
vs("assoc_focus", [(1, "Own group in the Netherlands"), (2, "Country of origin"), (3, "Both")])
vs("wants_friends4", [(1, "Yes, very much"), (2, "Yes"), (3, "No, rather not"), (4, "No, definitely not")])
vs("contact_balance", [(1, "More with own group"), (2, "Equally with both"), (3, "More with native Dutch")])
vs("residence4", [(1, "Same municipality"), (2, "Other municipality"), (3, "Country of origin"), (4, "Elsewhere")])
vs("parents_alive", [(1, "Both"), (2, "Father only"), (3, "Mother only"), (4, "Neither")])
vs("parent_asked", [(1, "Father"), (2, "Mother")])

# ---------------------------------------------------------------- attitudes
vs("annoy5", [(1, "Very annoying"), (2, "Annoying"), (3, "No opinion"), (4, "Not annoying"), (5, "Not at all annoying")])
vs("stay_home6", [(1, "Always the mother"), (2, "Mostly the mother"), (3, "Both"), (4, "Mostly the father"), (5, "Always the father"), (6, "Neither")])
vs("ideal_children", [(0, "No children"), (1, "1 child"), (2, "2 children"), (3, "3 children"), (4, "4 children"), (5, "5 children"), (8, "6 or more children")])
vs("child_value", [(1, "Obey parents"), (2, "Consideration / respect for others"), (3, "Independence")])
vs("neighbour_choice", [(1, "Compatriot"), (2, "Native Dutch"), (3, "Does not matter")])
vs("living_nl5", [(1, "Very pleasant"), (2, "Pleasant"), (3, "Neutral"), (4, "Unpleasant"), (5, "Very unpleasant")])
vs("safe5", [(1, "Very safe"), (2, "Safe"), (3, "Neither safe nor unsafe"), (4, "Unsafe"), (5, "Very unsafe")])
vs("parenting4", [(1, "Good"), (2, "Not so good"), (3, "Bad"), (4, "Very bad")])
vs("at_ease4", [(1, "Yes, very"), (2, "Yes, somewhat"), (3, "No, not really"), (4, "No, not at all")])

# ---------------------------------------------------------------- religion / identity / return
vs("religion_cat", [(0, "None"), (1, "Hinduism"), (2, "Islam"), (3, "Christianity"), (4, "Other")])
vs("religion_det", [(0, "No religion"),
                    (11, "Hindu: Sanatan Dharm"), (12, "Hindu: Arya Samaj"), (13, "Hindu: other / unspecified"),
                    (21, "Islam: Shia"), (22, "Islam: Sunni"), (23, "Islam: Alevi"), (24, "Islam: Ahmadiyya"), (25, "Islam: other / unspecified"),
                    (31, "Christian: Roman Catholic"), (32, "Christian: Dutch Reformed (Hervormd)"), (33, "Christian: Reformed (Gereformeerd)"),
                    (34, "Christian: Moravian (Evangelische Broedergemeente)"), (35, "Christian: Pentecostal"), (36, "Christian: Jehovah's Witness"),
                    (37, "Christian: Orthodox"), (38, "Christian: other / unspecified"), (39, "Christian: Protestant Church in the Netherlands (PKN)"),
                    (26, "Islam: Salafi (SIM 2011)"),
                    (41, "Jewish"), (42, "Zoroastrian"), (43, "Baha'i"), (44, "Sikh"), (45, "Buddhist"), (46, "Confucian"), (47, "Taoist"),
                    (99, "Other religion")])
vs("same_religion", [(1, "Same as raised in"), (2, "Different"), (3, "Not raised religiously")])
vs("attendance4", [(1, "Never"), (2, "A few times a year"), (3, "A few times a month"), (4, "Weekly or more")])
vs("iden_prim", [(1, "Own group"), (2, "Dutch")])
vs("iden_scale5", [(1, "Entirely own group"), (2, "More own group than Dutch"), (3, "Both equally"), (4, "More Dutch than own group"), (5, "Entirely Dutch")])
vs("iden_oth", [(0, "No"), (1, "Afghan"), (2, "Iraqi"), (3, "Iranian"), (4, "Yugoslav"), (5, "Somali"), (6, "Dutch"), (7, "Other people")])
vs("return3", [(1, "Yes"), (2, "Don't know"), (3, "No")])
vs("return_combined", [(1, "Wants to and able to return"), (2, "Wants to return, other"), (3, "Don't know"), (4, "Does not want to return")])
vs("reason_not_return", [(1, "Work"), (2, "Likes it here"), (3, "No money"), (4, "Study"), (5, "Political situation"), (6, "Children"),
                         (7, "No future in origin country"), (8, "No ties with origin country"), (9, "Health reasons / care (SPVA 2002)"), (10, "Other"),
                         (11, "Economic situation / no work in origin country (SIM)"), (12, "Origin country not a good place to live (SIM)"),
                         (13, "Born and raised in / long in the Netherlands (SIM)")])
vs("month_special", VALUESETS["month"])  # alias kept for clarity in some variables

# ================================================================ SIM 2015 / SIM 2020 additions
# ---- survey design
vs("mode", [(1, "Web (CAWI)"), (2, "Face-to-face (CAPI)"), (3, "Video interview (CAVI, SIM 2020)")])
vs("agency", [(1, "TNS NIPO / Veldkamp"), (2, "Labyrinth")])
vs("split_half", [(1, "Group A"), (2, "Group B")])
vs("qversion", [(1, "Version 1"), (2, "Version 2"), (3, "Version 3"), (4, "Version 4"), (5, "Version 5"), (6, "Version 6")])
vs("age_cat7", [(0, "Under 15 (SPVA/SPVN household members)"), (1, "15-24"), (2, "25-34"), (3, "35-44"), (4, "45-54"), (5, "55-64"), (6, "65-74"), (7, "75 or older"),
                (8, "70 or older, undivided (SIM 2011 top class)")])
vs("age_cat_chd4", [(1, "0-3"), (2, "4-12"), (3, "13-17"), (4, "18 or older")])
vs("cbs_origin3", [(1, "No migration background (native Dutch)"), (2, "Western migration background"), (3, "Non-western migration background")])
vs("marstat_reg", [(1, "Married / registered partnership"), (2, "Not married")])
vs("chd_residence", [(1, "All children in the Netherlands"), (2, "In the Netherlands and in the country of origin"),
                     (3, "All in the country of origin"), (4, "In another country"), (5, "In the Netherlands and in another country"), (6, "Various")])
vs("prtnr_activity", [(1, "Paid work"), (2, "Unemployed / job seeking"), (3, "Homemaker"), (4, "Work-disabled"),
                      (5, "Pupil / student"), (6, "Retired / state pension / early retirement"), (98, "Other")])
vs("oth_relation3", [(1, "No, not family"), (2, "Yes, family"), (3, "Family and non-family")])
vs("livsit5", [(1, "With partner, no children"), (2, "With partner and children"), (3, "Alone with children"),
               (4, "With parent(s) (child living at home)"), (98, "Other")])
vs("hh_type_reg", [(1, "One-person household"), (2, "Unmarried couple without children"), (3, "Married couple without children"),
                   (4, "Unmarried couple with children"), (5, "Married couple with children"), (6, "Single-parent household"),
                   (7, "Other household"), (8, "Institutional household"), (9, "Other / institutional / unknown (SIM 2020 classes)")])
vs("hh_pos_reg", [(1, "Child living at home"), (2, "Single"), (3, "Partner in unmarried couple without children"),
                  (4, "Partner in married couple without children"), (5, "Partner in unmarried couple with children"),
                  (6, "Partner in married couple with children"), (7, "Parent in single-parent household"),
                  (8, "Reference person in other household"), (9, "Other member of a household"), (10, "Member of institutional household"),
                  (19, "Reference person / other member / institutional / unknown (SIM 2020 classes)")])
# ---- housing
vs("tenure3", [(1, "Rented"), (2, "Owner-occupied"), (98, "Other")])
vs("tenure_reg", [(1, "Owner-occupied"), (2, "Rented"), (9, "Unknown")])
vs("landlord", [(1, "Housing association"), (2, "Private landlord"), (3, "Family, friend or acquaintance"), (4, "Employer"),
                (5, "Temp agency"), (6, "Student housing"), (98, "Other")])
vs("dwelling_type", [(1, "Independent rented or owned dwelling"), (2, "Room(s), sharing bathroom and/or kitchen with non-household members"),
                     (3, "Room in boarding house, hostel or hotel"), (4, "Holiday home or caravan on a campsite"), (5, "Housing unit (e.g. studio)"), (98, "Other")])
vs("urban5", [(1, "Very highly urbanised"), (2, "Highly urbanised"), (3, "Moderately urbanised"), (4, "Little urbanised"), (5, "Not urbanised")])
# ---- education
vs("edu3", [(0, "None / no diploma"), (1, "Low (primary, vmbo, mbo-1)"), (2, "Middle (havo/vwo, mbo 2-4)"), (3, "High (hbo, wo)")])
vs("edu3_att", [(1, "Low"), (2, "Middle"), (3, "High")])
vs("edu_where2", [(1, "In the country of origin"), (2, "In another country")])
vs("edu_parent4", [(1, "No education / never went to school"), (2, "Primary school"), (3, "Secondary school"), (4, "Higher education (hbo, university)")])
vs("enr_type_reg", [(1, "Secondary (vo)"), (2, "Upper vocational (mbo)"), (3, "Higher professional (hbo)"), (4, "University (wo)"),
                    (5, "Adult / vocational education (ve)"), (6, "Middle (vo/mbo) (SIM 2020 classes)"), (7, "High (hbo/wo) (SIM 2020 classes)")])
vs("inb_course3", [(1, "Followed"), (2, "Currently following"), (3, "Not followed")])
vs("inb_exam3", [(1, "Yes, passed"), (2, "No, preparing for the exam"), (3, "No")])
vs("nl_course5", [(1, "Yes, followed, no certificate"), (2, "Yes, followed and certified"), (3, "No, but planning to"), (4, "No"), (5, "Currently following")])
# ---- labour
vs("selfemp3", [(1, "Own business / self-employed"), (2, "Business of partner or parents"), (3, "Freelancer")])
vs("freq4_av", [(1, "Always"), (2, "Often"), (3, "Sometimes"), (4, "Never")])
vs("wants_work5", [(1, "Yes, 12 hours or more per week"), (2, "Yes, less than 12 hours per week"), (3, "No, not at the moment"),
                   (4, "Already found new work"), (5, "Would like to, but cannot")])
vs("sec_reg4", [(1, "Labour and capital"), (2, "Benefits"), (3, "Pension"), (4, "No income or unknown")])
vs("inc_band", [(1, "Less than 10,000 euro (SIM 2015: 2013 income)"), (2, "10,000-20,000"), (3, "20,000-30,000"), (4, "30,000-40,000"),
                (5, "40,000-50,000"), (6, "50,000 euro or more"),
                (11, "Less than 25,000 euro (SIM 2020: 2019 income)"), (12, "25,000-50,000"), (13, "50,000-75,000"), (14, "75,000-100,000"),
                (15, "100,000 euro or more"), (16, "75,000 euro or more (household, SIM 2020)"), (90, "No income"), (99, "Income unknown")])
vs("pct_band5", [(1, "1st-20th percentile"), (2, "21st-40th percentile"), (3, "41st-60th percentile"), (4, "61st-80th percentile"),
                 (5, "81st-100th percentile"), (6, "Institutional household or income unknown")])
# ---- migration (registry)
vs("ind_motive", [(10, "Family migration"), (11, "Family formation"), (12, "Family reunification"), (13, "Adoption / foster children"),
                  (20, "Asylum"), (30, "Labour"), (31, "Knowledge migrant"), (32, "Researcher"), (33, "Au pair"), (34, "Internship"),
                  (40, "Study"), (50, "Other"), (90, "Unknown / migrated within the same year")])
vs("ind_motive_pub", [(9, "Not applicable: EU/EFTA national (no IND motive)"), (10, "Family reunification"), (11, "Family formation"),
                      (20, "Asylum"), (30, "Other labour migration"), (31, "Knowledge migration"), (40, "Study"), (50, "Other motives")])
vs("ind_motive_nw", [(9, "Unknown (non-EU) / not applicable (EU/EFTA)"), (10, "Family reunification"), (11, "Family formation"),
                     (31, "Asylum: conditional residence permit (VVTV)"), (32, "Asylum: temporary/permanent permit"), (33, "Asylum: A-status"),
                     (34, "Asylum: other"), (35, "Asylum: unaccompanied minors (AMV)"), (40, "Knowledge migration"), (49, "Other labour migration"),
                     (51, "Au pair"), (61, "Study"), (71, "Economically inactive"), (81, "Medical treatment"), (91, "Other motives"), (99, "Unknown / not filled in")])
vs("motive_rank", [(1, "First migration goal"), (2, "Second"), (3, "Third"), (4, "Fourth")])
vs("future_res4", [(1, "Living in the Netherlands"), (2, "Partly in country of origin, partly in NL"), (3, "In the country of origin"), (4, "(Partly) in another country")])
vs("visit_dur3", [(1, "Less than a month"), (2, "One to three months"), (3, "More than three months")])
# ---- language / identification
vs("lang_prob4", [(1, "Often"), (2, "Sometimes"), (3, "Never"), (4, "Does not speak the language")])
vs("yes_bit_no", [(1, "Yes"), (2, "A little"), (3, "No")])
vs("strength5", [(1, "Very strongly"), (2, "Strongly"), (3, "A little"), (4, "Not"), (5, "Not at all")])
vs("home3", [(1, "Yes"), (2, "Sometimes"), (3, "No")])
# ---- social contacts
vs("freq5_cont", [(1, "Every day"), (2, "Every week"), (3, "Every month"), (4, "A few times a year"), (5, "Never / less than once a year")])
vs("freq4_vrsn", [(1, "Often"), (2, "Regularly"), (3, "Sometimes"), (4, "Never")])
vs("want_contact3", [(1, "Yes, more"), (2, "Fine as it is"), (3, "No, rather less")])
vs("share5", [(1, "Nobody"), (2, "Some"), (3, "Half"), (4, "Many"), (5, "All")])
vs("trust2", [(1, "Most people can be trusted"), (2, "You cannot be careful enough")])
vs("sport5", [(1, "Twice a week or more"), (2, "Once a week"), (3, "Once a month"), (4, "A few times a year"), (5, "Less than once a year / never")])
# ---- media
vs("media_freq5", [(1, "(Almost) every day"), (2, "Several times a week"), (3, "Once a week"), (4, "Less than once a week"), (5, "Never")])
vs("interest4", [(1, "Very interested"), (2, "Interested"), (3, "Not very interested"), (4, "Not at all interested")])
vs("amount3", [(1, "Too little"), (2, "Enough"), (3, "Too much")])
vs("positive5", [(1, "Very negative"), (2, "Negative"), (3, "Neutral"), (4, "Positive"), (5, "Very positive")])
# ---- politics
vs("trust4", [(1, "Very much trust"), (2, "Much trust"), (3, "Not so much trust"), (4, "No trust at all")])
vs("voted3", [(1, "Yes"), (2, "No"), (3, "Not eligible to vote")])
vs("vote_int5", [(1, "Yes"), (2, "Maybe"), (3, "No"), (4, "Not eligible to vote"), (5, "Prefers not to say (printed answer option: LAS 2004/05, SIM 2020)")])
vs("brthcntry_src", [(1, "Observed: country of birth collected in the survey"), (2, "Inferred from origin group x generation (CBS definition; public person-sample files carry no country of birth)")])
vs("party_nl", [(1, "VVD"), (2, "PVV"), (3, "CDA"), (4, "D66"), (5, "GroenLinks"), (6, "SP"), (7, "PvdA"), (8, "ChristenUnie"),
                (9, "Partij voor de Dieren"), (10, "50PLUS"), (11, "SGP"), (12, "DENK"), (13, "Forum voor Democratie"), (14, "Trots op Nederland / Verdonk (2011)"),
                (15, "Blank vote"), (16, "Does not know yet"), (17, "Would not vote"), (18, "LPF (SIM 2006)"), (92, "Other party")])
vs("understand3", [(1, "Much understanding"), (2, "A little understanding"), (3, "No understanding")])
vs("fear4", [(1, "Yes, afraid"), (2, "Yes, a little afraid"), (3, "No, not afraid"), (4, "No, not afraid, but it will happen")])
vs("tension3", [(1, "Yes, certainly"), (2, "Yes, maybe"), (3, "No")])
vs("problem5", [(1, "Very problematic"), (2, "Problematic"), (3, "Neutral"), (4, "Not problematic"), (5, "Not at all problematic")])
# ---- religion
vs("attendance5", [(1, "Every day"), (2, "Every week"), (3, "Every month"), (4, "A few times a year"), (5, "Never / less than once a year")])
vs("pray6", [(1, "Five times a day"), (2, "Every day"), (3, "Every week"), (4, "A few times a month"), (5, "A few times a year"), (6, "Never / less than once a year")])
vs("read5", [(1, "Every day"), (2, "Every week"), (3, "A few times a month"), (4, "A few times a year"), (5, "Never / less than once a year")])
vs("observe4", [(1, "Yes, every day"), (2, "Yes, most days"), (3, "Yes, some days"), (4, "No")])
# ---- discrimination
vs("freq4_disc", [(1, "No, never"), (2, "Yes, once or a few times"), (3, "Yes, fairly often"), (4, "Very often")])
# ---- health
vs("difficulty3", [(1, "Yes, much difficulty"), (2, "Yes, some difficulty"), (3, "No difficulty")])
vs("pain4", [(1, "Yes, much less well"), (2, "A little less well"), (3, "Hardly"), (4, "No, not at all")])
vs("freq4_mh", [(1, "Always"), (2, "Often"), (3, "Sometimes"), (4, "Never")])
vs("freq6_mhi", [(1, "All of the time"), (2, "Most of the time"), (3, "Often"), (4, "Sometimes"), (5, "Rarely"), (6, "Never")])
vs("freq4_lim", [(1, "All of the time"), (2, "Often"), (3, "Sometimes"), (4, "Never")])
vs("last_contact3", [(1, "Less than 12 months ago"), (2, "12 months ago or longer"), (3, "Never")])
vs("hospital3", [(1, "Yes, day admission only"), (2, "Yes, including overnight stay"), (3, "No")])
vs("care_rcv3", [(1, "Yes, from family, friends or acquaintances"), (2, "Yes, professional help (home care, domestic help)"), (3, "No")])
vs("relation8", [(1, "Partner"), (2, "Parent or step-parent"), (3, "Parent-in-law"), (4, "Child or step-child"), (5, "Other family member"),
                 (6, "Friend or acquaintance"), (7, "Neighbour"), (8, "Someone else")])

# ---------------------------------------------------------------- v0.4.0: LAS 2004/05, SIM 2006, SING 2009, SIM 2011
vs("lf3", [(1, "Employed labour force"), (2, "Unemployed labour force"), (3, "Not in the labour force")])
vs("change5", [(1, "Clearly improved"), (2, "Somewhat improved"), (3, "Unchanged"), (4, "Somewhat worsened"), (5, "Clearly worsened")])
vs("relative5", [(1, "Much better than others"), (2, "Somewhat better"), (3, "About the same"), (4, "Somewhat worse"), (5, "Much worse than others")])
vs("hh_income_band8", [(1, "Less than 500 euro per month"), (2, "500-1000 euro"), (3, "1000-1500 euro"), (4, "1500-2000 euro"),
                       (5, "2000-2500 euro"), (6, "2500-3000 euro"), (7, "3000-3500 euro"), (8, "More than 3500 euro per month")])
vs("inb_noreason", [(1, "No civic integration obligation"), (2, "Never summoned"), (3, "Followed another (language) course"),
                    (4, "On a waiting list / waiting for the municipality's offer"), (5, "No time / no interest"),
                    (6, "Not needed, got extra guidance or language lessons at school"), (7, "Exempted"), (8, "Other")])
vs("good4", [(1, "Good"), (2, "Reasonable"), (3, "Moderate"), (4, "Poor")])
vs("better3", [(1, "Better"), (2, "Equally well"), (3, "Worse")])
vs("lang_prob4_rw", [(1, "Often"), (2, "Sometimes"), (3, "Never"), (4, "Cannot read / write the language"), (5, "Not applicable: the language has no written form (SING 2009)")])
vs("nat_reason9", [(1, "Feels Dutch"), (2, "Passport, easier travel"), (3, "Work / social security"), (4, "To be able to vote"),
                   (5, "Did not choose, it happened automatically"), (6, "Lives here / belongs here"), (7, "Children get Dutch nationality"),
                   (8, "Arranged via / by parents"), (9, "Other")])
vs("ret_reason13", [(1, "No work in the Netherlands"), (2, "Discrimination"), (3, "Family in the country of origin"), (4, "No ties with the Netherlands"),
                    (5, "No future in the Netherlands"), (6, "Living in NL no longer pleasant / negative ideas about migrants"),
                    (7, "Better job chances in the country of origin"), (8, "Climate, good weather"), (9, "Atmosphere, contact between people"),
                    (10, "It is my fatherland / feel at home there"), (11, "Family / friends are there"), (12, "To live with partner"), (13, "Other")])
vs("visit3", [(1, "Yes, every year"), (2, "No, not every year"), (3, "No, never"), (4, "No, not possible to travel to the country of origin (SING 2009)"),
              (5, "No, no family left in the country of origin (SING 2009)")])
vs("ethmix4", [(1, "Mainly own origin group"), (2, "Mainly native Dutch"), (3, "Half own group, half native Dutch"), (4, "All kinds of groups"), (5, "Other (LAS 2004/05)")])
vs("grp_most6", [(1, "Moroccans"), (2, "Turks"), (3, "Antilleans / Arubans"), (4, "Surinamese"), (5, "Other group"), (6, "Mixed / various groups")])
vs("bestfriend4", [(1, "Own origin group"), (2, "Native Dutch"), (3, "Another minority group"), (4, "Has no best friend")])
vs("edu_lvl10", [(1, "Never went to school"), (2, "Primary school not completed"), (3, "Primary (lager onderwijs)"), (4, "Lower vocational (lbo/vbo)"),
                 (5, "Lower general secondary (mavo)"), (6, "Upper vocational (mbo)"), (7, "Upper general secondary (havo/vwo)"),
                 (8, "Higher professional (hbo)"), (9, "University (wo)"), (10, "Other")])
vs("edu_chd8", [(1, "Primary (basisonderwijs)"), (2, "vmbo basic / middle-management track"), (3, "vmbo theoretical / mixed track"),
                (4, "Upper vocational (mbo)"), (5, "havo/vwo"), (6, "Higher professional (hbo)"), (7, "University (wo)"), (8, "Other")])
vs("freq5_par", [(1, "Yes, always"), (2, "Yes, often"), (3, "Sometimes"), (4, "No, often not"), (5, "No, never")])
vs("true3", [(1, "Certainly true"), (2, "Somewhat true"), (3, "Not true")])
vs("quality5", [(1, "Very good"), (2, "Good"), (3, "Reasonable"), (4, "Not so good"), (5, "Bad")])
vs("important5", [(1, "Very important"), (2, "Important"), (3, "Neither important nor unimportant"), (4, "Unimportant"), (5, "Very unimportant")])
vs("freq3_adv", [(1, "Never"), (2, "Once"), (3, "Several times")])
vs("willing3", [(1, "Yes"), (2, "Maybe"), (3, "No")])
vs("parent_q3", [(1, "Continued with the questions for a parent"), (2, "Parents not present"), (3, "Parents refused")])
vs("charity4", [(1, "KWF Kankerbestrijding"), (2, "Wereld Natuur Fonds"), (3, "Unicef"), (4, "Villa Pardoes")])
vs("incentive2", [(1, "Gift voucher"), (2, "Money")])
vs("presence4", [(1, "Respondent interviewed alone"), (2, "Others present, no influence"), (3, "Others present, some influence"), (4, "Others present, much influence")])
vs("happy5", [(1, "Very happy"), (2, "Happy"), (3, "Neither happy nor unhappy"), (4, "Not so happy"), (5, "Unhappy")])
vs("interest3", [(1, "Very interested"), (2, "Somewhat interested"), (3, "Not interested")])
vs("effort4", [(1, "Yes, most do enough"), (2, "Neutral, so-so"), (3, "No, most do too little"), (4, "Some groups do, others do not")])
vs("integrated3", [(1, "Yes, enough"), (2, "Neutral, so-so"), (3, "No, too little")])
vs("disc_reason12", [(1, "Language"), (2, "Skin colour"), (3, "Ethnic group / origin"), (4, "Religion"), (5, "Surname"), (6, "Appearance (e.g. beard)"),
                     (7, "Headscarf"), (8, "Behaviour"), (9, "Sex"), (10, "Age"), (11, "Sexual orientation"), (12, "Other")])
vs("nbhd_reason10", [(1, "Found a pleasant dwelling here"), (2, "Dwelling allocated here"), (3, "Friends / family in the neighbourhood"),
                     (4, "Could afford a dwelling here"), (5, "Nice neighbourhood"), (6, "Convenient location"), (7, "Lives with parents"),
                     (8, "Moved in with partner"), (9, "Born here / lived here since childhood"), (10, "Other")])
vs("age_cat5y", [(1, "15-19"), (2, "20-24"), (3, "25-29"), (4, "30-34"), (5, "35-39"), (6, "40-44"), (7, "45-49"), (8, "50-54"), (9, "55-59"),
                 (10, "60-64"), (11, "65-69"), (12, "70 or older")])
vs("active3", [(1, "Very active"), (2, "Somewhat active"), (3, "Not / hardly active")])
vs("phase2", [(1, "Main phase"), (2, "Re-approach of non-respondents")])
vs("hours_cat5", [(0, "No hours"), (1, "Less than 12 hours per week"), (2, "12-19 hours"), (3, "20-34 hours"), (4, "35 hours or more")])
vs("remit_to6", [(1, "Partner / spouse"), (2, "Children"), (3, "Parents"), (4, "Other family members"), (5, "Others"), (6, "Organisations")])

# ---- v0.4.0: SIM 2006
vs("city_size6", [(1, "Small municipality"), (2, "Medium-sized municipality"), (3, "Amsterdam"), (4, "Rotterdam"), (5, "The Hague"), (6, "Utrecht")])
vs("hhpos4", [(1, "Head of household"), (2, "Partner of the head"), (3, "Lives with parents (co-resident child)"), (4, "Other")])
vs("accept4", [(1, "Certainly not"), (2, "Rather not"), (3, "Yes"), (4, "Certainly yes")])
vs("chance5", [(1, "Very large"), (2, "Large"), (3, "Neither large nor small"), (4, "Small"), (5, "Very small")])
vs("eq_chance_no8", [(1, "Does not speak Dutch well"), (2, "Prejudice / discrimination"), (3, "No suitable vacancies"), (4, "Knows too few people / fewer contacts"),
                     (5, "Health"), (6, "Too old"), (7, "Education too low / no diploma"), (8, "Other")])
vs("ease5", [(1, "Very easy"), (2, "Easy"), (3, "Neither easy nor difficult"), (4, "Difficult"), (5, "Very difficult")])
vs("amount_band9", [(1, "Less than 250 euro"), (2, "250-500 euro"), (3, "500-750 euro"), (4, "750-1000 euro"), (5, "1000-5000 euro"), (6, "5000-10,000 euro"),
                    (7, "10,000-20,000 euro"), (8, "20,000-50,000 euro"), (9, "More than 50,000 euro")])
vs("inc_band16", [(1, "Less than 500 euro per month"), (2, "500-750 euro"), (3, "750-1000 euro"), (4, "1000-1250 euro"), (5, "1250-1500 euro"), (6, "1500-1750 euro"),
                  (7, "1750-2000 euro"), (8, "2000-2250 euro"), (9, "2250-2500 euro"), (10, "2500-2750 euro"), (11, "2750-3000 euro"), (12, "3000-3250 euro"),
                  (13, "3250-3500 euro"), (14, "3500-5000 euro"), (15, "5000-7500 euro"), (16, "More than 7500 euro per month")])
vs("prob_type3", [(1, "Mainly speaking"), (2, "Mainly understanding"), (3, "Both")])
vs("org10", [(1, "Sports club"), (2, "Leisure organisation (hobby, music, theatre, dance)"), (3, "Neighbourhood or tenants' association"),
             (4, "Trade union / professional organisation"), (5, "Organisation of or for migrants"), (6, "Political party or organisation"),
             (7, "Religious organisation"), (8, "Nature, environment or international solidarity organisation"), (9, "Library"), (10, "Other organisation")])
vs("vol_for6", [(1, "For myself"), (2, "For my children"), (3, "For my neighbourhood / town"), (4, "For the origin group"), (5, "For society in general"), (6, "Other")])
vs("culture4", [(1, "Keep the origin culture entirely"), (2, "Keep the origin culture somewhat"), (3, "Adapt somewhat to Dutch culture"), (4, "Adapt entirely to Dutch culture")])
vs("media_days6", [(1, "Never"), (2, "Less than 1 day a week"), (3, "1-2 days a week"), (4, "3-4 days a week"), (5, "5-6 days a week"), (6, "Every day")])
vs("web_type5", [(1, "Mainly Dutch sites"), (2, "Mainly origin-country sites"), (3, "Both about equally"), (4, "Mainly Western (English/American) sites"), (5, "Other")])
vs("pol_where4", [(1, "Mainly Dutch politics"), (2, "Mainly origin-country politics"), (3, "Mainly politics of other countries"), (4, "All equally")])
vs("pay4", [(1, "The government entirely"), (2, "The government together with the participants"), (3, "The participants"), (4, "Depending on the participants' income")])
vs("pray7", [(1, "Never"), (2, "A few times a year"), (3, "A few times a month"), (4, "Once a week"), (5, "Several times a week"), (6, "Every day"), (7, "Five times a day or more")])
vs("veil_reason6", [(1, "Part of my faith"), (2, "Religious obligation"), (3, "Beautiful, symbol of beauty"), (4, "Sign of my Muslim identity"),
                    (5, "To avoid gossip or unpleasant behaviour"), (6, "Other")])
vs("noveil_reason6", [(1, "Not required by my faith"), (2, "One must be truly devout to wear it"), (3, "Not ready for it yet"), (4, "Better for integration in the Netherlands"),
                      (5, "Otherwise discrimination / unpleasant behaviour"), (6, "Other")])
vs("unsafe_freq3", [(1, "Often"), (2, "Sometimes"), (3, "Rarely")])
vs("limited3", [(1, "Yes, strongly"), (2, "Yes, slightly"), (3, "No")])
vs("alcohol5", [(1, "Never"), (2, "Almost never, not every week"), (3, "Some days"), (4, "Most days"), (5, "Every day")])

# ---- v0.4.0: LAS 2004/05
vs("hh_band16_las", [(1, "Less than 500 euro per month"), (2, "500-750 euro"), (3, "750-1000 euro"), (4, "1000-1250 euro"), (5, "1250-1500 euro"), (6, "1500-1750 euro"),
                     (7, "1750-2000 euro"), (8, "2000-2250 euro"), (9, "2250-2500 euro"), (10, "2500-2750 euro"), (11, "2750-3000 euro"), (12, "3000-3250 euro"),
                     (13, "3250-3500 euro"), (14, "3500-3750 euro"), (15, "3750-4000 euro"), (16, "More than 4000 euro per month")])
vs("flex3", [(1, "Yes, always"), (2, "Yes, within limits"), (3, "No")])
vs("avail4", [(1, "Within 2 weeks"), (2, "2 weeks to 3 months"), (3, "3 to 6 months"), (4, "6 months or longer")])
vs("seek3", [(1, "Yes"), (2, "No"), (3, "No, awaiting the result of an application")])
vs("freq5_conf", [(1, "No, never"), (2, "Yes, but rarely"), (3, "Yes, a few times a month"), (4, "Yes, a few times a week"), (5, "Yes, daily")])
vs("task_conflict5", [(1, "I do too little in the household"), (2, "My partner does too little"), (3, "According to my partner I do not do it well (enough)"),
                      (4, "My partner does not do it well (enough)"), (5, "Other")])
vs("plan5", [(1, "Certainly stop working"), (2, "Probably stop working"), (3, "Probably continue working"), (4, "Certainly continue working"), (5, "Did not know yet at the time")])
vs("care_opt5", [(1, "Ideal"), (2, "Good option"), (3, "Possibly"), (4, "Rather not"), (5, "Certainly not")])
vs("nocare14", [(1, "Not needed, respondent or partner always at home"), (2, "Prefers to look after the child him/herself"), (3, "Prefers grandparents or another trusted person"),
                (4, "Grandparents or other family live in or nearby"), (5, "Too expensive"), (6, "Waiting list too long"), (7, "Not in the neighbourhood"),
                (8, "Childcare too inflexible"), (9, "Child ill or disabled"), (10, "Considers the child too young (or too old / child does not want to)"),
                (11, "Already has childcare (at language course / with friends)"), (12, "Objections to or bad experience with nurseries or childminders"),
                (13, "Not familiar with nurseries / childminders or the subsidy"), (14, "No, inadequate or unintelligible answer")])
vs("leave_paid3", [(1, "Yes"), (2, "No"), (3, "With one employer yes, with the other no")])
vs("noleave14", [(1, "Partner has/had taken parental leave"), (2, "Did not want to lose too much income"), (3, "Does not know what parental leave is"),
                 (4, "Already working part-time, did not want to work less"), (5, "Enough (good) childcare available"), (6, "Partner has/had no work"), (7, "No work"),
                 (8, "Employer did not agree"), (9, "The work did not allow it"), (10, "Bad for my career"), (11, "Used days off"), (12, "Other"), (14, "None of these")])
vs("leave_type4", [(1, "Holiday or ADV days"), (2, "Special leave from the employer"), (3, "No leave taken, called in sick"), (4, "Other")])
vs("noleave_kz3", [(1, "Still had enough holiday / ADV days"), (2, "Did not know it was possible / did not know the scheme"), (3, "Other")])
vs("noleave_vry3", [(1, "Had too few days off"), (2, "Did not know the care-leave scheme"), (3, "Other")])
vs("freq5_month", [(1, "At least once a week"), (2, "2-3 times a month"), (3, "Once a month"), (4, "Less than once a month"), (5, "Rarely or never")])
vs("freq7_frnd", [(1, "Every day"), (2, "At least once a week"), (3, "2-3 times a month"), (4, "Once a month"), (5, "Less than once a month"), (6, "Rarely"),
                  (7, "Has no such friend or acquaintance")])
vs("ethmix5_las", [(1, "Mainly Western"), (2, "Mainly own origin group"), (3, "Half Western, half own group"), (4, "Diverse population groups"), (5, "Other")])
vs("lang3", [(1, "Dutch"), (2, "Mother tongue"), (3, "Another language")])
vs("lang_mix6", [(1, "Dutch"), (2, "More Dutch than mother tongue"), (3, "Dutch and mother tongue equally"), (4, "More mother tongue than Dutch"), (5, "Mother tongue"),
                 (6, "Mostly another language")])
vs("lang_mix7", [(1, "Dutch"), (2, "More Dutch than own language"), (3, "Dutch and own language equally"), (4, "More own language than Dutch"), (5, "Own language"),
                 (6, "English"), (7, "Mostly another language")])
vs("alone_org2", [(1, "Alone / on own"), (2, "Organised")])
vs("sport_n5", [(0, "Never"), (1, "1-11 times"), (2, "12-59 times"), (3, "60-119 times"), (4, "120 times or more")])
vs("sport26", [(1, "Athletics"), (2, "Motor sports"), (3, "Badminton"), (4, "Basketball"), (5, "Fitness / aerobics"), (6, "Golf"), (7, "Gymnastics"), (8, "Handball"),
               (9, "Hockey"), (10, "Korfball"), (11, "Horse riding"), (12, "Skating"), (13, "Inline skating"), (14, "Softball / baseball"), (15, "Squash"),
               (16, "Table tennis"), (17, "Tennis"), (18, "Cycling"), (19, "Jogging"), (20, "Martial arts"), (21, "Football"), (22, "Volleyball"), (23, "Walking"),
               (24, "Sailing / rowing / canoeing / surfing"), (25, "Swimming"), (26, "Other sport")])
vs("sportmem5", [(1, "No"), (2, "Sports club"), (3, "Sports school"), (4, "Fitness centre"), (5, "Other")])
vs("channel7", [(1, "Never watches this"), (2, "On Dutch channels"), (3, "More on Dutch than on origin-group channels"), (4, "On both kinds of channels"),
                (5, "More on origin-group than on Dutch channels"), (6, "On origin-group channels"), (7, "Other")])
vs("nonet6", [(1, "No interest, not important"), (2, "Computer too expensive"), (3, "Internet too expensive"), (4, "Too difficult"), (5, "Language problem"), (6, "Other")])
vs("nettype4", [(1, "Analogue modem"), (2, "ISDN"), (3, "Cable"), (4, "ADSL")])
vs("risk3", [(1, "Large"), (2, "Neither large nor small"), (3, "Small")])
vs("willing4", [(1, "Yes, definitely"), (2, "Yes, maybe"), (3, "Probably not"), (4, "Definitely not")])
vs("strict3", [(1, "Very strict"), (2, "Somewhat strict"), (3, "Not strict at all")])
vs("expel3", [(1, "Yes"), (2, "No"), (3, "It depends")])
vs("asylum_stay7", [(1, "If they have lived here long"), (2, "If the procedure took long"), (3, "If they have work"), (4, "If children were born here"),
                    (5, "If the situation in the origin country is unsafe"), (6, "Always, in all cases"), (7, "Other")])
vs("interest4_asc", [(1, "Not at all interested"), (2, "Little interested"), (3, "Fairly interested"), (4, "Strongly interested")])
vs("attendance6", [(1, "Never"), (2, "A few times a year"), (3, "A few times a month"), (4, "Once a week"), (5, "Several times a week"), (6, "Every day")])
vs("time_short3", [(1, "No, not at all"), (2, "Yes, a little"), (3, "Yes, very much")])
vs("weekday7", [(1, "Sunday"), (2, "Monday"), (3, "Tuesday"), (4, "Wednesday"), (5, "Thursday"), (6, "Friday"), (7, "Saturday")])
vs("act43", [(1, "Sleeping, resting"), (2, "Washing and dressing"), (3, "Preparing food and drink, setting the table"), (4, "Breakfast, lunch"), (5, "Dinner at home"),
             (6, "Caring for children"), (7, "Playing with children, reading to them"), (8, "Caring for other people"), (9, "Travelling by car"),
             (10, "Travelling by public transport"), (11, "Travelling by motorcycle, moped, scooter"), (12, "Travelling by bicycle"), (13, "Travelling on foot"),
             (14, "Paid work, incl. work at home"), (15, "Voluntary work"), (16, "School, attending lessons, lectures, courses"), (17, "Homework, studying"),
             (18, "Shopping (groceries)"), (19, "Going into town, shopping, being in the street"), (20, "Cleaning, tidying, washing up"), (21, "Laundry, ironing, sewing"),
             (22, "Maintenance, odd jobs, gardening"), (23, "Watching television / video / dvd"), (24, "Listening to radio / music"), (25, "Internet, e-mail, chatting"),
             (26, "Other computer use"), (27, "Church / mosque attendance, praying"), (28, "Sport"), (29, "Receiving visitors"), (30, "Visiting"),
             (31, "Visiting a restaurant, cafe, disco"), (32, "Visiting a coffee house, tea house"), (33, "Telephoning"), (34, "Reading"), (35, "Walking, cycling"),
             (36, "Visiting a zoo, recreation or amusement park"), (37, "Visiting a park, forest, heath, beach"), (38, "Visiting a museum, theatre, etc."),
             (39, "Games, handicrafts, making music, acting"), (40, "Doing nothing, lazing"), (41, "Drinking coffee"), (42, "Talking with household members"), (43, "Other")])
vs("earner8", [(1, "Sole earner: woman"), (2, "Sole earner: man"), (3, "One-and-a-half earners: woman full-time, man part-time"), (4, "Small one-and-a-half earners"),
               (5, "Large one-and-a-half earners"), (6, "Half and half"), (7, "Double earners"), (8, "No earners")])
vs("socpos9", [(1, "Unemployed / job seeking"), (2, "Homemaker"), (3, "Work-disabled (WAO)"), (4, "Pupil / student"), (5, "Working: elementary occupation"),
               (6, "Working: lower occupation"), (7, "Working: intermediate occupation"), (8, "Working: higher / scientific occupation"), (9, "Other")])
vs("hh_cbs7", [(1, "One-person household"), (2, "Unmarried couple (and others)"), (3, "Unmarried couple with children (and others)"), (4, "Married couple (and others)"),
               (5, "Married couple with children (and others)"), (6, "Single-parent family (and others)"), (7, "Non-family household")])
vs("who4", [(1, "Mostly the man"), (2, "Mostly the woman"), (3, "Both / together"), (4, "Someone else")])
vs("sector14", [(1, "Agriculture, fishing"), (3, "Manufacturing incl. mining"), (4, "Energy and water supply"), (5, "Construction"), (6, "Trade"), (7, "Hotels and catering"),
                (8, "Transport and communication"), (9, "Financial institutions"), (10, "Business services"), (11, "Public administration"), (12, "Education"),
                (13, "Health and welfare"), (14, "Culture and other services")])
vs("occ_class_las", [(11, "Elementary occupations"), (20, "Lower occupations n.e.c."), (33, "Lower: security / administrative, commercial"), (37, "Lower: care"),
                     (40, "Intermediate occupations n.e.c."), (42, "Intermediate: teachers"), (44, "Intermediate: agricultural"), (45, "Intermediate: mathematics, natural sciences"),
                     (46, "Intermediate: technical"), (48, "Intermediate: transport"), (49, "Intermediate: (para)medical"), (51, "Intermediate: administrative, commercial"),
                     (53, "Intermediate: legal, administrative, security"), (55, "Intermediate: linguistic, cultural"), (56, "Intermediate: behaviour and society"),
                     (57, "Intermediate: care"), (60, "Higher occupations n.e.c."), (62, "Higher: pedagogical"), (64, "Higher: agricultural"),
                     (65, "Higher: mathematics, natural sciences"), (66, "Higher: technical"), (68, "Higher: transport"), (69, "Higher: (para)medical"),
                     (71, "Higher: administrative, commercial, economic"), (73, "Higher: legal, administrative, security"), (75, "Higher: linguistic, cultural"),
                     (76, "Higher: behaviour and society"), (77, "Higher: care"), (78, "Higher: managers"), (80, "Scientific occupations n.e.c."),
                     (91, "Scientific: economic, administrative"), (93, "Scientific: legal, administrative"), (96, "Scientific: behaviour and society"),
                     (98, "Scientific: managers"), (99, "Not classifiable")])
vs("voucher2", [(1, "Blokker"), (2, "Free Record Shop")])
vs("pace3", [(1, "Already fairly well integrated"), (2, "Will integrate soon"), (3, "Will take a long time")])
vs("care_rcv_from4", [(1, "Parents or parents-in-law"), (2, "Other family members"), (3, "Neighbours"), (4, "Friends")])
vs("traffic8", [(1, "Parking"), (2, "Traffic jams and delays"), (3, "High costs (fuel, public transport fares)"), (4, "Accidents, speeding"), (5, "Aggression in traffic / public transport"),
                (6, "Exhaust fumes, traffic noise"), (7, "There are no problems"), (8, "Other")])

# ---- v0.4.0: SING 2009
# SING 2009 VERBLIJF: '0 tot 5 jaar' excludes 5 (the CBS years behind the classes: 0-4, 5-9, 10-14, 15+; restricted component, 4 Nov 2026)
vs("dur_cat4", [(1, "0-4 years"), (2, "5-9 years"), (3, "10-14 years"), (4, "15 years or more")])
vs("age_cat3", [(1, "15-24"), (2, "25-44"), (3, "45 or older")])
vs("hhpos3", [(1, "Head of household (male or female)"), (2, "Co-resident child"), (3, "Other")])
vs("when5", [(1, "Within a few months"), (2, "Within half a year"), (3, "Within a year"), (4, "In more than a year"), (5, "Does not know")])
vs("yr_cat7_mar", [(1, "1930-1950"), (2, "1951-1960"), (3, "1961-1970"), (4, "1971-1980"), (5, "1981-1990"), (6, "1991-2000"), (7, "2001-2009")])
vs("yr_cat5", [(1, "1930-1950"), (2, "1951-1970"), (3, "1971-1990"), (4, "1991-2000"), (5, "2001 or later")])
vs("yr_cat6_prtnr", [(1, "1930-1950"), (2, "1951-1970"), (3, "1971-1990"), (4, "1991-2000"), (5, "2001 or later"), (6, "At the same time as the respondent")])
vs("yr_cat5_doc", [(1, "1980-1985"), (2, "1986-1991"), (3, "1992-1997"), (4, "1998-2003"), (5, "2004-2009")])
vs("yr_cat5_stat", [(1, "1910-1930"), (2, "1931-1950"), (3, "1951-1970"), (4, "1971-1990"), (5, "1991 or later")])
vs("oth_rel11", [(1, "Father"), (2, "Mother"), (3, "Father-in-law / mother-in-law"), (4, "Brother / sister"), (5, "Grandfather / grandmother"), (6, "Nephew / niece / cousin"),
                 (7, "Other family"), (8, "Grandchild"), (9, "Partner's child / stepchild"), (10, "Friend / acquaintance"), (11, "Other")])
vs("months_cat6", [(1, "0 to 3 months"), (2, "4 to 10 months"), (3, "11 to 20 months"), (4, "21 to 35 months"), (5, "36 to 45 months"), (6, "46 months or longer")])
vs("inc_band14", [(1, "Less than 500 euro per month"), (2, "500-750 euro"), (3, "750-1000 euro"), (4, "1000-1250 euro"), (5, "1250-1500 euro"), (6, "1500-1750 euro"),
                  (7, "1750-2000 euro"), (8, "2000-2250 euro"), (9, "2250-2500 euro"), (10, "2500-2750 euro"), (11, "2750-3000 euro"), (12, "3000-3250 euro"),
                  (13, "3250-3500 euro"), (14, "More than 3500 euro per month"), (15, "No income from work or benefit (partner)")])
vs("enough4", [(1, "More than enough"), (2, "Enough"), (3, "Too little"), (4, "Far too little")])
vs("foreign4", [(1, "English"), (2, "German"), (3, "French"), (4, "None of these languages")])
vs("share2", [(1, "Own room (alone or with partner / family)"), (2, "Shares a room with others")])
vs("bmi4", [(1, "Underweight"), (2, "Healthy weight"), (3, "Overweight"), (4, "Obese")])
vs("when6_ret", [(1, "Within a year"), (2, "Within 1-2 years"), (3, "In 2 to 5 years"), (4, "In 5 to 10 years"), (5, "When my children are grown up"), (6, "When it is really safe again")])
vs("contact_vw3", [(1, "Yes, at the moment"), (2, "Yes, in the past, not any more"), (3, "No")])
