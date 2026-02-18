import json
from strength import calculate_strengths, get_karaka_info
from datetime import datetime

# Planet mapping to align with strength.py
planet_map_en_to_dev = {
    'Sun': 'सु', 'Moon': 'चं', 'Mars': 'मं', 'Mercury': 'बु', 'Jupiter': 'गु',
    'Venus': 'शु', 'Saturn': 'श', 'Rahu': 'रा',
    'Su': 'सु', 'Mo': 'चं', 'Ma': 'मं', 'Me': 'बु', 'Ju': 'गु',
    'Ve': 'शु', 'Sa': 'श', 'Ra': 'रा', 'Ke': 'के',
    'सु': 'सु', 'चं': 'चं', 'मं': 'मं', 'बु': 'बु', 'गु': 'गु',
    'शु': 'शु', 'श': 'श', 'रा': 'रा', 'के': 'के'
}

planet_map_dev_to_en = {
    'सु': 'Sun', 'चं': 'Moon', 'मं': 'Mars', 'बु': 'Mercury', 'गु': 'Jupiter',
    'शु': 'Venus', 'श': 'Saturn', 'रा': 'Rahu', 'के': 'Ketu'
}

# Planetary Strength Thresholds
STRONG_THRESHOLD = 60  # Percentage of ideal Shadbala
WEAK_THRESHOLD = 40

# Dasha Interpretation Database (updated with Devanagari codes)
DASHA_INTERPRETATIONS = {
    "सु": {
        "name": "Sun (Surya)",
        "general": {
            "positive": "नेतृत्व, अधिकार, जीवनशक्ति, आत्मविश्वास, सरकारी सफलता, पिता फिगर",
            "negative": "अहंकार टकराव, अहंकार, हृदय समस्या, सरकारी समस्या, पैतृक समस्या",
            "strong": "बलियो नेतृत्व, पहिचान, राम्रो स्वास्थ्य, अधिकारीहरूबाट समर्थन",
            "weak": "कम आत्मविश्वास, शक्ति संघर्ष, स्वास्थ्य समस्या (हृदय/हड्डी), पैतृक विवाद"
        },
        "antardashas": {
            "सु": {
                "duration": "6 months",
                "general": "सूर्य ऊर्जाको शिखर - नेतृत्व अवसर तर अहंकार चुनौती",
                "strong": "राजनीतिक सफलता, शाही कृपा, बलियो पैतृक समर्थन",
                "weak": "अधिकारवादी व्यवहार, हृदय समस्या, सरकारी द्वन्द्व"
            },
            "चं": {
                "duration": "10 months",
                "general": "अधिकारको भावनात्मक अभिव्यक्ति। सार्वजनिक छविमा उतारचढाव",
                "strong": "लोकप्रिय नेतृत्व, पालनपोषण गर्ने अधिकार ('पिता फिगर' जस्तै)",
                "weak": "मनोदशामा आधारित निर्णय, सार्वजनिक प्रतिष्ठा समस्या, पानी-सम्बन्धित स्वास्थ्य समस्या"
            },
            "मं": {
                "duration": "7 months",
                "general": "शक्तिको लागि आक्रामक पीछा। प्रतिस्पर्धी ऊर्जा",
                "strong": "सैन्य/पुलिस सफलता, एथलेटिक उपलब्धिहरू, साहसी नेतृत्व",
                "weak": "क्रोधित विस्फोट, दुर्घटना, अधिकारीहरूसँग द्वन्द्व"
            },
            "रा": {
                "duration": "18 months",
                "general": "अपरंपरागत शक्ति संघर्ष। अधिकारको परीक्षण",
                "strong": "क्रान्तिकारी नेतृत्व, नवीन शासन",
                "weak": "शक्ति कब्जा, घोटाला, पदबाट अचानक पतन"
            },
            "गु": {
                "duration": "16 months",
                "general": "नेतृत्वमा बुद्धि। आध्यात्मिक वा नैतिक शासन",
                "strong": "न्यायपूर्ण शासन, कानून/शिक्षामा सफलता, ईश्वरीय कृपा",
                "weak": "धार्मिक पाखण्ड, अधिकारमा खराब निर्णय"
            },
            "श": {
                "duration": "19 months",
                "general": "शक्तिमा प्रतिबन्ध। अधिकारमा कर्मिक पाठ",
                "strong": "संरचित नेतृत्व (सीईओ, प्रशासक), दीर्घकालीन योजना",
                "weak": "क्यारियरमा अवरोध, दमनकारी अधिकार, हड्डी/जोर्नी समस्या"
            },
            "बु": {
                "duration": "12 months",
                "general": "बौद्धिक नेतृत्व। अधिकारको सञ्चार",
                "strong": "सञ्चार मार्फत प्रभावकारी शासन, लेखनमा सफलता",
                "weak": "शक्तिको गलत सञ्चार, स्नायु तनाव"
            },
            "के": {
                "duration": "9 months",
                "general": "शक्तिबाट वैराग्य। अधिकारको आध्यात्मिकीकरण",
                "strong": "प्रबुद्ध नेतृत्व, पदमा अनासक्ति",
                "weak": "अचानक स्थिति गुमाउनु, जीवनको उद्देश्य बारे भ्रम"
            },
            "शु": {
                "duration": "20 months",
                "general": "शक्तिको कलात्मक अभिव्यक्ति। नेतृत्वमा विलासिता",
                "strong": "शाही कला, कूटनीतिक सफलता, सुमधुर अधिकार",
                "weak": "पतित नेतृत्व, सुखको लागि शक्तिको दुरुपयोग"
            }
        }
    },
    "चं": {
        "name": "Moon (Chandra)",
        "general": {
            "positive": "भावनात्मक वृद्धि, मातृत्व, सार्वजनिक सम्बन्ध, अन्तर्ज्ञान, पोषण",
            "negative": "मुड स्विङ्स, चिन्ता, पानी-सम्बन्धित समस्या, मातृ समस्या",
            "strong": "बलियो अन्तर्ज्ञान, भावनात्मक स्थिरता, लोकप्रियता, पालनपोषण गर्ने क्षमता",
            "weak": "भावनात्मक अस्थिरता, समर्थनको अभाव, पाचन समस्या, सार्वजनिक अस्वीकृति"
        },
        "antardashas": {
            "चं": {
                "duration": "10 months",
                "general": "उच्च भावनात्मकता र संवेदनशीलता। घर/आमाको फिगरमा ध्यान",
                "strong": "मानसिक क्षमता, बलियो मातृ सम्बन्ध, सफल हेरचाह",
                "weak": "भावनात्मक विघटन, आमाको स्वास्थ्य समस्या, पानी-सम्बन्धित दुर्घटना"
            },
            "सु": {
                "duration": "6 months",
                "general": "अधिकारको भावनात्मक अभिव्यक्ति। सार्वजनिक छविमा उतारचढाव",
                "strong": "लोकप्रिय नेतृत्व, सहजता सहितको पालनपोषण गर्ने अधिकार ('पिता फिगर' जस्तै)",
                "weak": "मनोदशामा आधारित निर्णय, सार्वजनिक प्रतिष्ठा समस्या, पानी-सम्बन्धित स्वास्थ्य समस्या"
            },
            "मं": {
                "duration": "7 months",
                "general": "भावनात्मक साहस। भावनात्मक तर अस्थिर मुड",
                "strong": "सुरक्षात्मक प्रवृत्ति (जस्तै, आमाले बच्चाको रक्षा गर्ने), प्रेरित भावनाहरू",
                "weak": "क्रोधित विस्फोट, आवेगपूर्ण भावनात्मक निर्णय, रगत-सम्बन्धित समस्या"
            },
            "रा": {
                "duration": "18 months",
                "general": "अपरंपरागत भावनाहरू। कर्मिक आमा-बच्चा सम्बन्ध",
                "strong": "मानसिक सफलता, गैर-परम्परागत उपचार",
                "weak": "भावनात्मक हेरफेर, पलायनवादको लत"
            },
            "गु": {
                "duration": "16 months",
                "general": "भावनाहरूमा बुद्धि। आध्यात्मिक पोषण",
                "strong": "मातृ बुद्धि, नर्सिङ/शिक्षणमा सफलता, ईश्वरीय अन्तर्ज्ञान",
                "weak": "आमाको अत्यधिक आदर्शकरण, धार्मिक भावनात्मक निर्भरता"
            },
            "श": {
                "duration": "19 months",
                "general": "भावनात्मक प्रतिबन्ध। सम्बन्धमा शीतलता",
                "strong": "भावनात्मक अनुशासन (जस्तै, चिकित्सकको वैराग्य)",
                "weak": "अवसाद, एक्लोपन, आमाबाट उपेक्षा"
            },
            "बु": {
                "duration": "12 months",
                "general": "बौद्धिक भावनाहरू। परिवर्तनशील विचार/मुड",
                "strong": "काव्य अभिव्यक्ति, भावनाहरूको राम्रो सञ्चार",
                "weak": "स्नायु चिन्ता, भावनाहरूको अत्यधिक सोच"
            },
            "के": {
                "duration": "9 months",
                "general": "भावनात्मक वैराग्य। आध्यात्मिक चाहना",
                "strong": "योगिक वैराग्य, गहन सपना/दर्शन",
                "weak": "भावनात्मक शून्यता, परित्यागका मुद्दाहरू"
            },
            "शु": {
                "duration": "20 months",
                "general": "कलात्मक भावनाहरू। रोमान्टिक संवेदनशीलता",
                "strong": "संगीत/कलात्मक प्रतिभा, सुमधुर सम्बन्ध",
                "weak": "सुखमा अत्यधिक लिप्तता, प्रेममा भावनात्मक निर्भरता"
            }
        }
    },
    "मं": {
        "name": "Mars (Mangal)",
        "general": {
            "positive": "साहस, पहल, एथलेटिक्स, शल्य चिकित्सा परिशुद्धता, रक्षा, प्रतिस्पर्धामा सफलता",
            "negative": "दुर्घटना, हिंसा, जलन, द्वन्द्व, आवेगपूर्ण कार्य, रगत विकार",
            "strong": "चुनौतीहरूमा विजय, संकटमा नेतृत्व, बलियो जीवनशक्ति",
            "weak": "पुरानो क्रोध, आत्म-विनाश, सूजन, हतियार-सम्बन्धित चोटहरू"
        },
        "antardashas": {
            "मं": {
                "duration": "7 months",
                "general": "उच्चतम मंगल ऊर्जा - उच्च जोखिम/इनाम अवधि",
                "strong": "सैन्य/पुलिस पदोन्नति, इन्जिनियरिङ सफलता, एथलेटिक रेकर्ड",
                "weak": "गम्भीर दुर्घटना, कानूनी लडाई, विस्फोटक स्वभाव"
            },
            "रा": {
                "duration": "18 months",
                "general": "अपरंपरागत आक्रामकता। कर्मिक युद्ध",
                "strong": "क्रान्तिकारी युद्ध रणनीति, अत्याधुनिक प्रविधि",
                "weak": "आतंकवादमा संलग्नता, विकिरण जलन, अराजक हिंसा"
            },
            "गु": {
                "duration": "16 months",
                "general": "अनुशासित कार्य। आध्यात्मिक योद्धा ऊर्जा",
                "strong": "कानूनी लडाईहरूमा सफलता, नैतिक सैनिक, धर्मको प्रवर्तन",
                "weak": "धार्मिक अतिवाद, अधिकारको दुरुपयोग"
            },
            "श": {
                "duration": "19 months",
                "general": "प्रतिबन्धित आक्रामकता। दीर्घकालीन रणनीति",
                "strong": "धैर्यवान युद्ध (घेराबन्दी रणनीति), संरचनात्मक इन्जिनियरिङ",
                "weak": "कुण्ठित ऊर्जा जसले पुरानो दुखाइ वा अवसाद निम्त्याउँछ"
            },
            "बु": {
                "duration": "12 months",
                "general": "रणनीतिक सञ्चार। मानसिक तीक्ष्णता",
                "strong": "शानदार बहस कौशल, बोलीमा शल्य चिकित्सा परिशुद्धता",
                "weak": "व्यंग्यात्मक आक्रमण, स्नायु प्रणाली ओभरलोड"
            },
            "के": {
                "duration": "9 months",
                "general": "वैरागी कार्य। रहस्यमय योद्धा चरण",
                "strong": "एक्यूपंक्चरमा निपुणता, मानसिक शल्य चिकित्सा क्षमता",
                "weak": "अस्पष्ट घाउ, ऊर्जा चुहावट"
            },
            "शु": {
                "duration": "20 months",
                "general": "उत्साहपूर्ण अभिव्यक्ति। कलात्मक आक्रामकता",
                "strong": "मार्शल आर्ट्स कोरियोग्राफी, प्रतिस्पर्धात्मक कला",
                "weak": "हिंसक कामुकता, कस्मेटिक सर्जरीमा दुर्घटना"
            },
            "सु": {
                "duration": "6 months",
                "general": "अधिकारपूर्ण कार्य। संकटमा नेतृत्व",
                "strong": "वीर नेतृत्व, सरकारी सैन्य भूमिका",
                "weak": "तानाशाही प्रवृत्ति, लू लाग्ने"
            },
            "चं": {
                "duration": "10 months",
                "general": "भावनात्मक साहस। सुरक्षात्मक प्रवृत्ति",
                "strong": "मातृ रक्षा (बाघिनी ऊर्जा), साहसी हेरचाह",
                "weak": "हिस्टेरिकल प्रतिक्रिया, आत्म-हानि प्रवृत्ति"
            }
        }
    },
    "बु": {
        "name": "Mercury (Budha)",
        "general": {
            "positive": "बुद्धि, सञ्चार, वाणिज्य, गणित, अनुकूलनशीलता, हास्य",
            "negative": "चिन्ता, छल, स्नायु विकार, बोलीमा दोष, चञ्चलता",
            "strong": "शानदार सञ्चार, सफल वार्ता, तीखो सिकाइ",
            "weak": "गलत सूचना, धोका, सिकाइ असक्षमता, प्राविधिक असफलता"
        },
        "antardashas": {
            "बु": {
                "duration": "12 months",
                "general": "उच्चतम मानसिक गतिविधि - तीव्र सञ्चार अवधि",
                "strong": "लेखन/बोल्नमा सफलता, सफल व्यापार सम्झौता",
                "weak": "जानकारीको अधिकता, करार विवाद, ग्याजेटमा खराबी"
            },
            "के": {
                "duration": "9 months",
                "general": "सहज ज्ञान। गैर-मौखिक सञ्चार",
                "strong": "मानसिक लेखन, कम्प्युटर प्रोग्रामिङ प्रतिभा",
                "weak": "सञ्चारमा अवरोध, भ्रमपूर्ण सन्देश"
            },
            "शु": {
                "duration": "20 months",
                "general": "कलात्मक सञ्चार। वित्तीय बुद्धि",
                "strong": "काव्य अभिव्यक्ति, सफल वित्तीय विश्लेषण",
                "weak": "कलात्मक चोरी, वित्तीय गलत रिपोर्टिङ"
            },
            "सु": {
                "duration": "6 months",
                "general": "अधिकारपूर्ण सञ्चार। विचारमा नेतृत्व",
                "strong": "शक्तिशाली भाषण, सरकारी ठेक्का",
                "weak": "अहंकारी लेखन, सौर्य चक्रमा घबराहट"
            },
            "चं": {
                "duration": "10 months",
                "general": "भावनात्मक बुद्धि। परिवर्तनशील विचार",
                "strong": "मनोविज्ञान कौशल, लोकप्रिय लेखन",
                "weak": "मनोदशामा आधारित राय, अविश्वसनीय स्मृति"
            },
            "मं": {
                "duration": "7 months",
                "general": "आक्रामक सञ्चार। प्राविधिक ध्यान",
                "strong": "बहसमा जीत, इन्जिनियरिङ समाधान",
                "weak": "मौखिक आक्रमण, लापरवाह ड्राइभिङ (मानसिक हतार)"
            },
            "रा": {
                "duration": "18 months",
                "general": "अपरंपरागत सोच। डिजिटल क्रान्ति",
                "strong": "आविष्कारक विचार, सामाजिक सञ्जालमा सफलता",
                "weak": "ह्याकिङ, पहिचान चोरी, झूटा समाचार"
            },
            "गु": {
                "duration": "16 months",
                "general": "सञ्चारमा बुद्धि। नैतिक व्यापार",
                "strong": "शिक्षणमा सफलता, कानूनी करारमा निपुणता",
                "weak": "अत्यधिक आशावादी पूर्वानुमान, गुरु घोटाला"
            },
            "श": {
                "duration": "19 months",
                "general": "संरचित सोच। ढिलो सञ्चार",
                "strong": "वैज्ञानिक अनुसन्धान, सावधानीपूर्वक विश्लेषण",
                "weak": "सिकाइमा अवरोध, नोकरशाही झन्झट"
            }
        }
    },
    "शु": {
        "name": "Venus (Shukra)",
        "general": {
            "positive": "प्रेम, सुन्दरता, कला, विलासिता, विवाह, कामुक सुख, रचनात्मकता",
            "negative": "आलस्य, घमण्ड, सुखको लत, यौन अधिकता, वित्तीय बर्बाद",
            "strong": "कलात्मक प्रतिभा, सुमधुर सम्बन्ध, रचनात्मक प्रतिभाबाट धन",
            "weak": "भंग भएका सम्बन्ध, कलात्मक अवरोध, विलासितामा वित्तीय हानि"
        },
        "antardashas": {
            "शु": {
                "duration": "20 months",
                "general": "उच्चतम रचनात्मक र रोमान्टिक ऊर्जा",
                "strong": "कलात्मक उत्कृष्ट कृतिहरू, ईश्वरीय प्रेम अनुभवहरू",
                "weak": "बाध्यकारी सुख, कस्मेटिक सर्जरीमा दुर्घटना"
            },
            "सु": {
                "duration": "6 months",
                "general": "रोमान्टिक अधिकार। प्रेम-शक्ति गतिशीलता",
                "strong": "शाही कला संरक्षण, सौन्दर्य उद्योगहरूमा नेतृत्व",
                "weak": "अहंकारी प्रेम सम्बन्ध, सूर्य-सम्बन्धित छालाका समस्याहरू"
            },
            "चं": {
                "duration": "10 months",
                "general": "भावनात्मक कलात्मकता। सार्वजनिक आकर्षण",
                "strong": "लोकप्रिय कलात्मकता, पालनपोषण गर्ने प्रेम",
                "weak": "मनोदशामा आधारित सौन्दर्य मापदण्ड, भावनात्मक निर्भरता"
            },
            "मं": {
                "duration": "7 months",
                "general": "उत्साहपूर्ण रचनात्मकता। यौन ऊर्जा",
                "strong": "कामुक कला, सफल कस्मेटिक सर्जरी",
                "weak": "हिंसक कामुकता, सौन्दर्य उद्योगका घोटाला"
            },
            "रा": {
                "duration": "18 months",
                "general": "अपरंपरागत सुन्दरता। निषेधित सम्बन्ध",
                "strong": "अग्रगामी कला आन्दोलनहरू, रूपान्तरणकारी प्रेम",
                "weak": "यौन लत, असामान्य सौन्दर्य उपचार"
            },
            "गु": {
                "duration": "16 months",
                "general": "नैतिक विलासिता। आध्यात्मिक सौन्दर्यशास्त्र",
                "strong": "मन्दिर कला, नैतिक फेसनमा सफलता",
                "weak": "भौतिकवादी आध्यात्मिकता, गुरु घोटाला"
            },
            "श": {
                "duration": "19 months",
                "general": "संरचित सुन्दरता। ढिलो प्रेम सम्बन्ध",
                "strong": "शास्त्रीय कला पुनर्स्थापना, दीर्घकालीन साझेदारी",
                "weak": "प्रेमको अभाव, कलामा वित्तीय अवरोध"
            },
            "बु": {
                "duration": "12 months",
                "general": "कलात्मक सञ्चार। वित्तीय आकर्षण",
                "strong": "काव्य प्रतिभा, सफल कला बिक्री",
                "weak": "कलात्मक चोरी, वित्तीय धोका"
            },
            "के": {
                "duration": "9 months",
                "general": "रहस्यमय सुन्दरता। प्रेम वैराग्य",
                "strong": "पवित्र ज्यामितीय निपुणता, तान्त्रिक कला",
                "weak": "प्रेममा मोहभंग, असामान्य सौन्दर्य विकार"
            }
        }
    },
    "श": {
        "name": "Saturn (Shani)",
        "general": {
            "positive": "अनुशासन, दीर्घायु, कडा परिश्रम, आध्यात्मिक वृद्धि, संरचनात्मक निपुणता",
            "negative": "ढिलाइ, अवसाद, गरिबी, पुरानो रोग, एक्लोपन",
            "strong": "अटल धैर्य, कर्मिक पुरस्कार, समयमाथि निपुणता",
            "weak": "कठोर प्रतिबन्ध, परित्याग, कंकाल विकार"
        },
        "antardashas": {
            "श": {
                "duration": "19 months",
                "general": "उच्चतम कर्मिक लेखाजोखा - जीवन संरचनाको परीक्षण",
                "strong": "वास्तुकला उपलब्धिहरू, आध्यात्मिक अनुशासन",
                "weak": "गम्भीर एक्लोपन, वित्तीय अवरोध, हड्डी भाँच्ने"
            },
            "बु": {
                "duration": "12 months",
                "general": "संरचित सञ्चार। व्यावहारिक बुद्धि",
                "strong": "वैज्ञानिक लेखन, सावधानीपूर्वक वित्तीय योजना",
                "weak": "सिकाइ असक्षमता, नोकरशाही निराशा"
            },
            "के": {
                "duration": "9 months",
                "general": "कर्मिक वैराग्य। रहस्यमय तपस्या",
                "strong": "उन्नत योग अभ्यास, पूर्व-जन्मको ज्ञान",
                "weak": "अस्पष्ट थकान, आध्यात्मिक भ्रम"
            },
            "शु": {
                "duration": "20 months",
                "general": "अनुशासित कलात्मकता। परिपक्व सम्बन्ध",
                "strong": "शास्त्रीय कला निपुणता, दीर्घकालीन साझेदारी",
                "weak": "यौन दमन, कलात्मक अवरोध"
            },
            "सु": {
                "duration": "6 months",
                "general": "कठिनाइबाट अधिकार। पिता figures को परीक्षण",
                "strong": "सम्मानित जेष्ठ स्थिति, सरकारी पेन्सन",
                "weak": "अहंकार चूर हुने, हृदय परिसंचरण समस्या"
            },
            "चं": {
                "duration": "10 months",
                "general": "भावनात्मक परिपक्वता। मातृ पाठ",
                "strong": "मनोवैज्ञानिक गहिराई, पैतृक उपचार",
                "weak": "भावनात्मक स्थिर हुने, आमाको स्वास्थ्य संकट"
            },
            "मं": {
                "duration": "7 months",
                "general": "नियन्त्रित आक्रामकता। रणनीतिक द्वन्द्व",
                "strong": "सैन्य इन्जिनियरिङ, शल्य चिकित्सा परिशुद्धता",
                "weak": "पुरानो दुखाइ, दबिएको क्रोध विस्फोट"
            },
            "रा": {
                "duration": "18 months",
                "general": "अपरंपरागत प्रतिबन्ध। कर्मिक क्रान्ति",
                "strong": "दमनकारी प्रणाली तोड्ने, अपरंपरागत उपचार",
                "weak": "कालो तन्त्रको खतरा, औद्योगिक दुर्घटना"
            },
            "गु": {
                "duration": "16 months",
                "general": "कठिनाइबाट ज्ञान। आध्यात्मिक न्याय",
                "strong": "कर्मिक नियम बुझ्ने, गुरुहरूसँग धैर्य",
                "weak": "धार्मिक पाखण्ड उदाङ्गो हुने, कानूनी ढिलाइ"
            }
        }
    },
    "रा": {
        "name": "Rahu (North Node)",
        "general": {
            "positive": "नवीनता, विदेशी सम्बन्ध, प्राविधिक निपुणता, भौतिक महत्वाकांक्षा, भ्रम नियन्त्रण",
            "negative": "लत, नशा, छल, अराजकता, अनियन्त्रित इच्छाहरू",
            "strong": "अपरंपरागत मार्गबाट ​​उन्नति, विदेश वा प्राविधिक उद्योगहरूमा सफलता",
            "weak": "घोटाला, वास्तविकताबाट विच्छेद, धोखाधडी, मनोवैज्ञानिक अस्थिरता"
        },
        "antardashas": {
            "रा": {
                "duration": "32 months",
                "general": "उच्चतम कर्मिक उथलपुथल। छाया रूपान्तरण अवधि",
                "strong": "जीवनमा ठूला फड्को, उच्च नवीनता",
                "weak": "अचानक पतन, कर्मिक प्रतिशोध"
            },
            "गु": {
                "duration": "16 months",
                "general": "नैतिक विस्तार र भ्रमको भेट",
                "strong": "आध्यात्मिक सफलताहरू, भेषमा बुद्धि",
                "weak": "पाखण्ड, झूटा गुरुहरू, अन्धो विश्वास"
            },
            "श": {
                "duration": "19 months",
                "general": "भौतिक यथार्थवाद र भ्रमको टकराव",
                "strong": "संरचित महत्वाकांक्षा, शक्तिशाली विश्वव्यापी भूमिका",
                "weak": "अत्यधिक चिन्ता, नोकरशाही अराजकता"
            },
            "बु": {
                "duration": "12 months",
                "general": "मानसिक तीव्रता र हेरफेर",
                "strong": "प्रतिभा स्तरको बुद्धि, कोडिङ/ह्याकिङमा सफलता",
                "weak": "मानसिक थकान, झूट बोल्ने बानी"
            },
            "के": {
                "duration": "9 months",
                "general": "छाया युद्ध। अहंकार विघटन संघर्ष",
                "strong": "मानसिक जागरण, कर्मिक समाधान",
                "weak": "मनोविकार, पूर्ण विच्छेद"
            },
            "शु": {
                "duration": "20 months",
                "general": "इच्छा र कामुकताको भेट। प्रेमका भ्रम",
                "strong": "ग्ल्यामर/फिल्म/मिडिया संसारमा सफलता",
                "weak": "लत, अनैतिक सम्बन्ध"
            },
            "सु": {
                "duration": "6 months",
                "general": "अहंकार बनाम भ्रम। अस्थायी अधिकार",
                "strong": "करिश्माई नेतृत्व, प्रसिद्धिको उदय",
                "weak": "आत्ममोह, शक्तिबाट पतन"
            },
            "चं": {
                "duration": "10 months",
                "general": "भावनात्मक भ्रम। पारिवारिक कर्म",
                "strong": "मातृ घाउ निको पार्ने, पैतृक मुक्ति",
                "weak": "मनोदशा विकार, मातृ भ्रम"
            },
            "मं": {
                "duration": "7 months",
                "general": "आक्रामक कर्म। अराजक कार्य",
                "strong": "साहसी सुधार, क्रान्तिकारी साहस",
                "weak": "हिंसक प्रवृत्ति, मेसिनरीबाट खतरा"
            }
        }
    },
    "के": {
        "name": "Ketu (South Node)",
        "general": {
            "positive": "वैराग्य, आध्यात्मिक अन्तर्दृष्टि, मोक्ष, रहस्यमय ज्ञान, शल्य चिकित्सा परिशुद्धता",
            "negative": "भ्रम, एक्लोपन, पलायनवाद, अनावश्यक हानि",
            "strong": "गहिरो ज्ञान, मानसिक बोध, सन्यासमा सफलता",
            "weak": "मानसिक अस्थिरता, आत्महत्याको विचार, परित्यागका मुद्दाहरू"
        },
        "antardashas": {
            "के": {
                "duration": "9 months",
                "general": "उच्चतम वैराग्य। आध्यात्मिक जागरण वा भित्री अराजकता",
                "strong": "ज्ञानोदयका क्षणहरू, चमत्कारहरू",
                "weak": "मानसिक विघटन, कर्मिक हानि"
            },
            "शु": {
                "duration": "20 months",
                "general": "वैरागी प्रेम। अहंकार बिना कला",
                "strong": "दिव्य सौन्दर्य, रहस्यमय रचनात्मकता",
                "weak": "भावनात्मक निकासी, मोहभंग भएको प्रेम सम्बन्ध"
            },
            "सु": {
                "duration": "6 months",
                "general": "अहंकारको हानि। दिव्य नम्रता",
                "strong": "आत्म-बोध, शक्तिशाली भित्री जागरण",
                "weak": "पहिचान संकट, स्वास्थ्य समस्या"
            },
            "चं": {
                "duration": "10 months",
                "general": "भावनात्मक मुक्ति। कर्मिक पारिवारिक शुद्धीकरण",
                "strong": "पैतृक आघातबाट निको हुने",
                "weak": "भावनात्मक शून्यता, आमाबाट विच्छेद"
            },
            "मं": {
                "duration": "7 months",
                "general": "आध्यात्मिक योद्धा। सटीक ऊर्जा",
                "strong": "शल्य चिकित्सा कौशल, आध्यात्मिक अनुशासन",
                "weak": "लुकेका चोटहरू, लापरवाह वैराग्य"
            },
            "रा": {
                "duration": "18 months",
                "general": "छाया द्वन्द्व। भूतकाल बनाम भविष्य",
                "strong": "कर्मिक एकीकरण, मानसिक निपुणता",
                "weak": "दिग्भ्रम, सिजोफ्रेनियाका लक्षण"
            },
            "गु": {
                "duration": "16 months",
                "general": "रहस्यमय ज्ञान। वैरागी शिक्षा",
                "strong": "गुरुजस्तो वैराग्य, गहिरो दर्शन",
                "weak": "सिद्धान्तवादी पलायनवाद, अन्धो आध्यात्मिक अहंकार"
            },
            "श": {
                "duration": "19 months",
                "general": "कर्तव्य र वैराग्यको भेट",
                "strong": "आध्यात्मिक अनुशासन, उद्देश्य सहित सन्यास",
                "weak": "अवसाद, कर्मिक दुःख"
            },
            "बु": {
                "duration": "12 months",
                "general": "मानसिक वैराग्य। विच्छेदित तर्क",
                "strong": "तीव्र अन्तर्ज्ञान, आध्यात्मिक सञ्चार",
                "weak": "मौखिक मौनता, संज्ञानात्मक कुहिरो"
            }
        }
    },
    "गु": {
        "name": "Jupiter (Guru)",
        "general": {
            "positive": "ज्ञान, वृद्धि, आध्यात्मिकता, धन, शिक्षा, सन्तान, नैतिकता, विस्तार",
            "negative": "अत्यधिक आशावादी, फजूल खर्च, धार्मिक कट्टरता, तौल बढ्ने, कानूनी समस्या",
            "strong": "शिक्षा/आध्यात्मिकतामा सफलता, ईश्वरीय कृपा, आर्थिक प्रचुरता",
            "weak": "खराब निर्णय, वित्तीय हानि, गुरुहरूसँग विवाद, अत्यधिक भोग"
        },
        "antardashas": {
            "गु": {
                "duration": "16 months",
                "general": "आध्यात्मिक वृद्धि, धन संचय, र उच्च शिक्षाको लागि अत्यन्तै शुभ अवधि",
                "strong": "ईश्वरीय आशीर्वाद, तीर्थयात्राका अवसर, शिक्षण/पुरोहित्याइँमा सफलता",
                "weak": "झूटा गुरुहरू, अनुष्ठानमा पैसा बर्बाद, विश्वासमा अत्यधिक आत्मविश्वास"
            },
            "श": {
                "duration": "19 months",
                "general": "अनुशासन आवश्यक पर्ने मिश्रित परिणाम। ढिलो तर स्थायी पुरस्कार",
                "strong": "संरचित आध्यात्मिक अभ्यास (योग, ध्यान), कर्मिक पाठ सिकेका",
                "weak": "गम्भीर प्रतिबन्ध, अपेक्षाहरू पूरा नहुँदा अवसाद, पुरानो स्वास्थ्य समस्या"
            },
            "बु": {
                "duration": "12 months",
                "general": "शिक्षण/लेखन मार्फत बौद्धिक वृद्धि। व्यापार सञ्चार फस्टाउँछ",
                "strong": "सफल प्रकाशन, शैक्षिक उद्यम, नैतिक व्यापार सम्झौता",
                "weak": "आदर्शहरूको गलत सञ्चार, अध्ययनमा धोका, अनैतिक विज्ञापन"
            },
            "के": {
                "duration": "9 months",
                "general": "आध्यात्मिक वैराग्य तर भौतिक भ्रम। अप्रत्याशित घटनाहरू",
                "strong": "रहस्यमय अनुभवहरू, गैर-भौतिकवादी ज्ञान, मानसिक अन्तर्दृष्टि",
                "weak": "विश्वासको हानि, नक्कली आध्यात्मिक व्यक्तिहरूद्वारा ठगी, समाजबाट अलगाव"
            },
            "शु": {
                "duration": "20 months",
                "general": "मूल्यहरूसँग मिल्ने विलासिता, परिष्कृत सुख, र कलात्मक अभिव्यक्ति",
                "strong": "पवित्र कला (मन्दिर संगीत/नृत्य), सुमधुर सम्बन्ध, नैतिक धन",
                "weak": "भौतिकवादी आध्यात्मिकता, कामुक अत्यधिक भोग, विद्यार्थीहरूसँग प्रेम सम्बन्ध"
            },
            "सु": {
                "duration": "6 months",
                "general": "आध्यात्मिक/शैक्षिक क्षेत्रमा नेतृत्व। ज्ञानको लागि पहिचान",
                "strong": "सम्मानित अधिकार, धार्मिक संस्थाहरूको लागि सरकारी समर्थन",
                "weak": "गुरुहरूसँग अहंकार टकराव, शिक्षण भूमिकामा शक्तिको दुरुपयोग, कलेजो समस्या"
            },
            "चं": {
                "duration": "10 months",
                "general": "परम्परा मार्फत भावनात्मक पूर्ति। पारिवारिक रीतिरिवाजले महत्त्व पाउँछ",
                "strong": "मातृ आशीर्वाद, पैतृक ज्ञान, सहज शिक्षण क्षमता",
                "weak": "भावनात्मक अन्धविश्वास, निर्णयलाई असर गर्ने मुड स्विङ्स, पानी-सम्बन्धित समस्या"
            },
            "मं": {
                "duration": "7 months",
                "general": "विश्वासको लागि साहसी कार्य। सिद्धान्तहरूमा सम्भावित द्वन्द्व",
                "strong": "धर्मको रक्षा (धार्मिक कारणहरू), खेलकुद/योगमा सफलता",
                "weak": "धार्मिक युद्ध, तीर्थयात्राको क्रममा चोटपटक, आवेगपूर्ण दान"
            },
            "रा": {
                "duration": "18 months",
                "general": "अपरंपरागत आध्यात्मिक मार्गहरू। अराजकता मार्फत विश्वासको परीक्षण",
                "strong": "वैदिक अनुसन्धानमा सफलता, नवीन शिक्षण विधिहरू",
                "weak": "साम्प्रदायिक वा चरमपन्थी गुट, प्रतिष्ठा गुमाउनु, विदेशी कानूनी समस्या"
            }
        }
    }
    # Add other planets' interpretations as needed
}

def get_interpretation_with_strength(maha, antar, pratyantar, strength_percent):
    """Get interpretation adjusted for planetary strength"""
    maha_dev = planet_map_en_to_dev.get(maha, maha)
    antar_dev = planet_map_en_to_dev.get(antar, antar)
    pratyantar_dev = planet_map_en_to_dev.get(pratyantar, pratyantar)

    # Validate dasha entries
    if maha_dev not in DASHA_INTERPRETATIONS:
        return {"error": f"No interpretation available for Mahadasha {maha_dev}"}
    if antar_dev not in DASHA_INTERPRETATIONS[maha_dev]["antardashas"]:
        return {"error": f"No interpretation available for Antardasha {antar_dev} in {maha_dev}"}

    base_interpretation = DASHA_INTERPRETATIONS[maha_dev]["antardashas"][antar_dev]
    
    # Determine strength key
    strength_key = (
        "strong" if strength_percent >= STRONG_THRESHOLD else
        "weak" if strength_percent <= WEAK_THRESHOLD else
        "general"
    )
    
    interpretation = {
        "period": f"{planet_map_dev_to_en.get(maha_dev, maha_dev)} Mahadasha → "
                 f"{planet_map_dev_to_en.get(antar_dev, antar_dev)} Antardasha → "
                 f"{planet_map_dev_to_en.get(pratyantar_dev, pratyantar_dev)} Pratyantar",
        "duration": base_interpretation["duration"],
        "main_theme": base_interpretation["general"],
        "strength_adjusted": base_interpretation.get(strength_key, base_interpretation["general"]),
        "strength_percent": f"{strength_percent:.2f}%",
        "advice": generate_advice(maha_dev, antar_dev, strength_percent)
    }
    
    return interpretation

def generate_advice(maha, antar, strength):
    """Generate practical advice based on dasha and strength"""
    advice = []
    maha_dev = planet_map_en_to_dev.get(maha, maha)
    antar_dev = planet_map_en_to_dev.get(antar, antar)
    
    if maha_dev == "गु":  # Jupiter
        if antar_dev == "गु":
            advice.append("ध्यान र योग मार्फत आध्यात्मिक अध्ययन र नैतिक नेतृत्वमा ध्यान दिनुहोस्।")
            if strength < WEAK_THRESHOLD:
                advice.append("आध्यात्मिक गुरुहरूलाई पछ्याउनु अघि तिनीहरूको विश्वसनीयता जाँच गर्नुहोस्।")
        elif antar_dev == "श":
            advice.append("आध्यात्मिक अभ्यासहरू (जस्तै योग, ध्यान) को लागि संरचित दिनचर्या लागू गर्नुहोस्।")
            if strength > STRONG_THRESHOLD:
                advice.append("तपाईंको अनुशासनले दीर्घकालीन बुद्धि सिर्जना गर्नेछ।")
        elif antar_dev == "शु":
            advice.append("कलात्मक र नैतिक धन संचयमा ध्यान दिनुहोस्।")
            if strength < WEAK_THRESHOLD:
                advice.append("भौतिकवादी आध्यात्मिकता र अत्यधिक भोगबाट बच्नुहोस्।")
        elif antar_dev == "सु":
            advice.append("आध्यात्मिक र शैक्षिक नेतृत्वमा ध्यान दिनुहोस्।")
            if strength < WEAK_THRESHOLD:
                advice.append("अहंकार टकराव र शक्तिको दुरुपयोगबाट बच्नुहोस्।")
        elif antar_dev == "चं":
            advice.append("परम्परा र पारिवारिक रीतिरिवाजलाई सम्मान गर्नुहोस्।")
            if strength < WEAK_THRESHOLD:
                advice.append("भावनात्मक अस्थिरताबाट बच्न ध्यान र शान्त रहने अभ्यास गर्नुहोस्।")
        elif antar_dev == "मं":
            advice.append("विश्वास र सिद्धान्तको रक्षा गर्न साहसी कदम चाल्नुहोस्।")
            if strength < WEAK_THRESHOLD:
                advice.append("आवेगपूर्ण कार्य र द्वन्द्वबाट बच्नुहोस्।")
        elif antar_dev == "रा":
            advice.append("नवीन आध्यात्मिक मार्गहरू अन्वेषण गर्नुहोस्।")
            if strength < WEAK_THRESHOLD:
                advice.append("चरमपन्थी विचार र समूहहरूबाट सावधान रहनुहोस्।")
        elif antar_dev == "बु":
            advice.append("शिक्षण र लेखन मार्फत ज्ञान बाँड्नुहोस्।")
            if strength < WEAK_THRESHOLD:
                advice.append("गलत सञ्चार र धोकाबाट बच्न सावधानी अपनाउनुहोस्।")
        elif antar_dev == "के":
            advice.append("आध्यात्मिक वैराग्य र गैर-भौतिकवादी दृष्टिकोण अपनाउनुहोस्।")
            if strength < WEAK_THRESHOLD:
                advice.append("नक्कली आध्यात्मिक मार्गदर्शकहरूबाट सावधान रहनुहोस्।")
    
    # Add advice for other planets
    if maha_dev == "सु":
        if antar_dev == "सु":
            advice.append("नेतृत्व र आत्मविश्वासलाई प्राथमिकता दिनुहोस्।")
            if strength < WEAK_THRESHOLD:
                advice.append("अहंकार र सरकारी समस्याबाट बच्नुहोस्।")
        elif antar_dev == "चं":
            advice.append("भावनात्मक नेतृत्व र सार्वजनिक सम्बन्धमा ध्यान दिनुहोस्।")
            if strength < WEAK_THRESHOLD:
                advice.append("मनोदशामा आधारित निर्णयबाट बच्नुहोस्।")
    
    # Extend for other Mahadashas and Antardashas similarly
    
    return advice if advice else [
        "वर्तमान समयमा तपाईंको जीवनमा घटिरहेका साना ठूला घटनाहरूलाई ध्यानपूर्वक हेरेर कर्मले सिकाउन चाहेको पाठ सिक्ने र मनबाट बुझ्ने प्रयास गर्नुहोस्। "
        "साथै, नियमित आउने र जाने श्वास-प्रश्वासको प्रक्रियालाई होशपूर्वक अवलोकन गर्ने प्रयास गर्नुहोस्। - सौरभ बराल"
    ]

def interpret_dasha_sequence(jd, positions, planet_speeds, divisional_dignities, phala_weights, 
                            maha, antar, pratyantar):
    """Interpret provided dasha sequence with strength analysis and generate HTML output"""
    try:
        # 1. Calculate planetary strengths
        table1_data, bala_breakdown = calculate_strengths(
            jd, positions, planet_speeds or {}, divisional_dignities or {}, phala_weights or {}, include_nodes=True
        )

        # 2. Get karaka information
        karaka_info = get_karaka_info(positions, include_nodes=True, include_eighth_karaka=True)

        # 3. Map dasha planets to Devanagari codes
        maha_dev = planet_map_en_to_dev.get(maha, maha)
        antar_dev = planet_map_en_to_dev.get(antar, antar)
        pratyantar_dev = planet_map_en_to_dev.get(pratyantar, pratyantar)

        # 4. Get strength for the Mahadasha planet
        strength_percent = 0
        for row in table1_data:
            planet_dev = planet_map_en_to_dev.get(row[0], row[0])
            if planet_dev == maha_dev:
                strength_percent = float(row[3].replace('%', ''))
                break

        # 5. Get interpretation
        interpretation = get_interpretation_with_strength(
            maha_dev, antar_dev, pratyantar_dev, strength_percent
        )

        # 6. Generate HTML for display
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Mangal, Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                h2 {{ color: #333; }}
            </style>
        </head>
        <body>
            <h2>Dasha Interpretation</h2>
            <table>
                <tr><th>Period</th><td>{interpretation.get('period', 'N/A')}</td></tr>
                <tr><th>Duration</th><td>{interpretation.get('duration', 'N/A')}</td></tr>
                <tr><th>Main Theme</th><td>{interpretation.get('main_theme', 'N/A')}</td></tr>
                <tr><th>Strength-Adjusted Effect</th><td>{interpretation.get('strength_adjusted', 'N/A')}</td></tr>
                <tr><th>Strength</th><td>{interpretation.get('strength_percent', 'N/A')}</td></tr>
                <tr><th>Advice</th><td>{'<br>'.join(interpretation.get('advice', []))}</td></tr>
            </table>
            <h2>Planetary Strengths</h2>
            <table>
                <tr><th>Planet</th><th>Rank</th><th>Total</th><th>Final %</th><th>Ishta</th><th>Kashta</th><th>Status</th><th>State</th></tr>
        """
        for row in table1_data:
            html_content += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{row[5]}</td><td>{row[6]}</td><td>{row[7]}</td></tr>"
        html_content += """
            </table>
            <h2>Chara Karakas</h2>
            <table>
                <tr><th>Karaka</th><th>Planet</th><th>Position</th></tr>
        """
        for k in karaka_info:
            html_content += f"<tr><td>{k['Karaka']}</td><td>{planet_map_dev_to_en.get(k['Planet'], k['Planet'])}</td><td>{k['Position']}</td></tr>"
        html_content += """
            </table>
        </body>
        </html>
        """

        return {
            "interpretation": interpretation,
            "strengths": table1_data,
            "karakas": karaka_info,
            "html": html_content
        }

    except Exception as e:
        return {"error": f"Error in dasha interpretation: {str(e)}"}