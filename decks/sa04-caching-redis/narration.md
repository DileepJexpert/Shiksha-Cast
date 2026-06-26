# SA04 — Caching Aur Redis Basics — App Ko Fast Kaise Banaye?

_Read / explain each slide using these notes._

## Slide 1

दोस्तों, सोचिए आपका app बहुत slow है. हर बार जब कोई user अपनी profile खोलता है, app database में जाकर वही data दोबारा-दोबारा निकालता है. लाखों users पर database हाँफने लगता है. क्या हो अगर बार-बार माँगा जाने वाला data हम कहीं पास में, तेज़ जगह रख लें? यही है caching का जादू, और इसका सबसे popular tool है Redis. System design interviews में ये बहुत पूछा जाता है. आज Katixo KhojLab की इस episode में हम साफ़ Hinglish में caching और Redis के basics समझेंगे. चलिए शुरू करते हैं।

## Slide 2

सबसे पहले — Caching है क्या? Caching मतलब बार-बार इस्तेमाल होने वाले data की एक copy किसी तेज़ जगह पर रख लेना, ताकि अगली बार उसे slow original source से निकालना ना पड़े. आम तौर पर ये fast जगह होती है memory यानी RAM, जो disk-based database से कई गुना तेज़ है. आसान भाषा में, cache एक shortcut है — जो data आप बार-बार माँगते हो, उसे हाथ के पास रख लो, ताकि हर बार पूरा सफ़र ना करना पड़े.

## Slide 3

इसे एक analogy से समझते हैं. सोचिए आपकी रसोई और बाज़ार. हर बार चाय बनाने के लिए आप बाज़ार जाकर चीनी नहीं लाते — आप थोड़ी चीनी रसोई के डिब्बे में रख लेते हो. बाज़ार है आपका database, धीमा पर पूरा भंडार. रसोई का डिब्बा है आपका cache, छोटा पर एकदम पास और तेज़. जब चीनी ख़त्म हो, तभी बाज़ार जाते हो. Caching का पूरा idea यही है — common चीज़ें पास रखो, rare चीज़ों के लिए ही दूर जाओ.

## Slide 4

अब Redis को मिलते हैं. Redis का पूरा नाम है Remote Dictionary Server. ये एक in-memory data store है, मतलब ये data मुख्य रूप से RAM में रखता है, इसीलिए ये बेहद तेज़ है — microseconds में जवाब. इसे आमतौर पर key-value store की तरह use किया जाता है, यानी हर data के साथ एक unique key, जैसे एक dictionary जिसमें शब्द और उसका मतलब. Redis open source है और दुनिया भर में caching के लिए सबसे ज़्यादा इस्तेमाल होता है.

## Slide 5

Redis सिर्फ़ simple text नहीं रखता, ये कई data structures support करता है, यही इसकी असली ताकत है. Strings — simple key-value, जैसे एक user का नाम. Hashes — एक object जैसे पूरी user profile एक key में. Lists — ordered items, जैसे एक queue. Sets — unique items का group. और Sorted Sets — score के साथ, जो leaderboards के लिए perfect है. इसी variety की वजह से Redis सिर्फ़ cache नहीं, बहुत कुछ बन जाता है.

## Slide 6

अब सबसे important pattern — Cache-Aside, जो interviews में सबसे ज़्यादा पूछा जाता है. जब data चाहिए, app पहले cache में देखता है. अगर मिल गया, इसे Cache Hit कहते हैं, data तुरंत वापस — बहुत तेज़. अगर नहीं मिला, इसे Cache Miss कहते हैं, तब app database में जाता है, वहाँ से data लाता है, उसे cache में रख देता है अगली बार के लिए, और फिर user को देता है. यही read-through जैसा सबसे common caching flow है.

## Slide 7

अब एक बहुत ज़रूरी concept — TTL यानी Time To Live. Cache में रखे हर data के साथ हम एक expiry time set कर सकते हैं, जैसे 60 second या 1 घंटा. उस समय के बाद Redis उस data को अपने आप हटा देता है. ये क्यों ज़रूरी है? ताकि cache में हमेशा ताज़ा data रहे और वो database से बहुत पुराना ना हो जाए. TTL के बिना cache में stale यानी बासी data पड़ा रह सकता है, जो users को गलत जानकारी दिखा सकता है.

## Slide 8

अब caching की सबसे बड़ी चुनौती — Cache Invalidation, यानी जब original data बदल जाए तो cache को कैसे update या हटाएँ. एक मशहूर कहावत है — computer science में दो ही मुश्किल चीज़ें हैं, और उनमें से एक है cache invalidation. मान लो user ने अपना नाम बदला, database update हो गया, पर cache में पुराना नाम पड़ा है. इसलिए जब data बदले, या तो cache की entry delete कर दो, या नई value से update कर दो. ये सही से ना करो तो users को गलत data दिखेगा.

## Slide 9

अब एक concrete example से पूरा flow जोड़ते हैं. एक user अपनी profile खोलता है. App पहले Redis में key user colon 123 ढूँढता है. पहली बार ये miss होता है, तो app database से profile लाता है, उसे Redis में 5 minute के TTL के साथ रख देता है. अगले 5 minute तक जितनी बार वही profile खुलेगी, सीधे Redis से super-fast मिलेगी, database को छुएगी भी नहीं. जब user profile edit करे, app उस key को delete कर देता है ताकि अगली बार fresh data आए.

## Slide 10

अब एक ज़रूरी सावधानी, क्योंकि Redis data RAM में रखता है, जो limited और महँगी होती है. इसलिए सब कुछ cache मत करो — सिर्फ़ वो data जो बार-बार पढ़ा जाता है पर कम बदलता है, जैसे product details या profiles. एक और concept — Eviction. जब memory भर जाए, Redis पुरानी entries हटाता है, अक्सर LRU policy से, यानी जो सबसे कम हाल में इस्तेमाल हुई. और हाँ, Redis data को disk पर save भी कर सकता है, इसे persistence कहते हैं, पर इसका मुख्य role तेज़ी ही है.

## Slide 11

अब interview points समेट लेते हैं. Redis cache के अलावा और भी कामों में आता है — session storage, यानी users के login sessions रखना, rate limiting के counters, leaderboards sorted sets से, और एक basic message broker या pub-sub के तौर पर. एक common सवाल — Redis vs Memcached. दोनों in-memory हैं, पर Redis ज़्यादा data structures, persistence, और features देता है, जबकि Memcached सिर्फ़ simple key-value caching के लिए हल्का और सीधा है. Interview में हमेशा बताइए कि caching का मकसद है latency घटाना और database का load कम करना.

## Slide 12

तो चलिए एक quick recap कर लेते हैं, तीन points में. पहला — Caching बार-बार माँगे जाने वाले data की copy एक तेज़ जगह, अक्सर RAM में, रखता है ताकि app fast हो और database पर load घटे. दूसरा — Redis एक in-memory key-value store है, जो strings, hashes, lists, sets जैसे data structures support करता है, और TTL के साथ data रखता है. तीसरा — सबसे common pattern है cache-aside, और सबसे बड़ी चुनौती है cache invalidation और stale data से बचना.

## Slide 13

तो दोस्तों, आज आपने सीखा कि caching कोई छोटी optimization नहीं, बल्कि हर fast और scalable system का एक core हिस्सा है, और Redis इसका सबसे भरोसेमंद साथी. अगली बार जब आपका app slow लगे, सोचिए — क्या यहाँ caching लग सकती है? Interview में cache hit, miss, TTL और invalidation जैसे शब्द confidently बोलिए, impression पक्का है. एक बार खुद Redis install करके key-value try करें, सब clear हो जाएगा. Aisi aur system design videos ke liye Katixo KhojLab subscribe karein! मिलते हैं अगली episode में।

