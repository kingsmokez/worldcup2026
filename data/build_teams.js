const fs = require('fs');

const existing = JSON.parse(fs.readFileSync('d:/UI/world/data/teams.json', 'utf8'));
const teamsMap = {};
existing.teams.forEach(t => { teamsMap[t.code] = t; });

// Remove POL, ITA, DEN, SRB
const removeCodes = ['POL', 'ITA', 'DEN', 'SRB'];
removeCodes.forEach(c => delete teamsMap[c]);

// Update groups for existing teams
const groupUpdates = {
  'USA': 'D', 'MEX': 'A', 'GHA': 'L',
  'ARG': 'J', 'NED': 'F', 'SEN': 'I', 'AUS': 'D',
  'FRA': 'I', 'COL': 'K', 'KOR': 'A', 'MAR': 'C',
  'ENG': 'L', 'URU': 'H', 'SUI': 'B', 'QAT': 'B',
  'BRA': 'C', 'CRO': 'L', 'EGY': 'G', 'CAN': 'B',
  'GER': 'E', 'POR': 'K', 'ECU': 'E', 'JPN': 'F',
  'ESP': 'H', 'IRN': 'G', 'BEL': 'G', 'CIV': 'E', 'KSA': 'H'
};
Object.entries(groupUpdates).forEach(([code, group]) => {
  if (teamsMap[code]) teamsMap[code].group = group;
});

// New teams data
const newTeams = [
  {
    code: "RSA", name: "South Africa", name_zh: "南非", group: "A", flag_emoji: "🇿🇦",
    elo_rating: 1620, fifa_rank: 55, confederation: "CAF", formation: "4-4-2",
    key_players: [
      {name: "Percy Tau", position: "LW"},
      {name: "Lyle Foster", position: "ST"},
      {name: "Teboho Mokoena", position: "CDM"},
      {name: "Ronwen Williams", position: "GK"},
      {name: "Themba Zwane", position: "CAM"}
    ],
    squad: [
      {number: 1, name: "Ronwen Williams", name_zh: "罗恩文·威廉姆斯", position: "GK", position_zh: "门将"},
      {number: 2, name: "Nyiko Mobbie", name_zh: "莫比", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "Terrence Mashego", name_zh: "马谢戈", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Mothobi Mvala", name_zh: "姆瓦拉", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Grant Kekana", name_zh: "凯卡纳", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Teboho Mokoena", name_zh: "特博霍·莫科埃纳", position: "CDM", position_zh: "后腰"},
      {number: 7, name: "Percy Tau", name_zh: "珀西·陶", position: "LW", position_zh: "左边锋"},
      {number: 8, name: "Themba Zwane", name_zh: "坦巴·兹瓦内", position: "CAM", position_zh: "前腰"},
      {number: 9, name: "Lyle Foster", name_zh: "莱尔·福斯特", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Evidence Makgopa", name_zh: "马科戈帕", position: "ST", position_zh: "前锋"},
      {number: 11, name: "Zakhele Lepasa", name_zh: "莱帕萨", position: "RW", position_zh: "右边锋"},
      {number: 12, name: "Sipho Chaine", name_zh: "谢内", position: "GK", position_zh: "门将"},
      {number: 13, name: "Sphephelo Sithole", name_zh: "西索勒", position: "CM", position_zh: "中前卫"},
      {number: 14, name: "Mihlali Mayambela", name_zh: "马扬贝拉", position: "LW", position_zh: "左边锋"},
      {number: 15, name: "Nkosinathi Sibisi", name_zh: "西比西", position: "CB", position_zh: "中后卫"},
      {number: 16, name: "Tapelo Xoki", name_zh: "肖基", position: "CB", position_zh: "中后卫"},
      {number: 17, name: "Kamohelo Mahlatsi", name_zh: "马赫拉齐", position: "CM", position_zh: "中前卫"},
      {number: 18, name: "Khuliso Mudau", name_zh: "穆达乌", position: "RB", position_zh: "右后卫"},
      {number: 19, name: "Relebohile Mofokeng", name_zh: "莫福肯", position: "RW", position_zh: "右边锋"},
      {number: 20, name: "Ricardo Goss", name_zh: "戈斯", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WLDWWLLDWW", goals_scored_last10: 11, goals_conceded_last10: 10
  },
  {
    code: "CZE", name: "Czech Republic", name_zh: "捷克", group: "A", flag_emoji: "🇨🇿",
    elo_rating: 1720, fifa_rank: 35, confederation: "UEFA", formation: "4-2-3-1",
    key_players: [
      {name: "Patrik Schick", position: "ST"},
      {name: "Vladimír Coufal", position: "RB"},
      {name: "Tomáš Souček", position: "CM"},
      {name: "Adam Hložek", position: "LW"},
      {name: "David Zima", position: "CB"}
    ],
    squad: [
      {number: 1, name: "Jindřich Staněk", name_zh: "斯塔内克", position: "GK", position_zh: "门将"},
      {number: 2, name: "Vladimír Coufal", name_zh: "库法尔", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "David Zima", name_zh: "齐马", position: "CB", position_zh: "中后卫"},
      {number: 4, name: "Tomáš Holeš", name_zh: "霍莱什", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Robin Hranáč", name_zh: "赫拉纳奇", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Tomáš Souček", name_zh: "绍切克", position: "CM", position_zh: "中前卫"},
      {number: 7, name: "Antonín Barák", name_zh: "巴拉克", position: "CAM", position_zh: "前腰"},
      {number: 8, name: "Adam Hložek", name_zh: "赫洛热克", position: "LW", position_zh: "左边锋"},
      {number: 9, name: "Patrik Schick", name_zh: "希克", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Lukáš Provod", name_zh: "普罗沃德", position: "CM", position_zh: "中前卫"},
      {number: 11, name: "Václav Černý", name_zh: "切尔尼", position: "RW", position_zh: "右边锋"},
      {number: 12, name: "Vít Václav", name_zh: "瓦茨拉夫", position: "GK", position_zh: "门将"},
      {number: 13, name: "Mojmír Chytil", name_zh: "希蒂尔", position: "ST", position_zh: "前锋"},
      {number: 14, name: "Ondřej Lingr", name_zh: "林格尔", position: "CM", position_zh: "中前卫"},
      {number: 15, name: "Matěj Vydra", name_zh: "维德拉", position: "ST", position_zh: "前锋"},
      {number: 16, name: "Jan Bořil", name_zh: "博日尔", position: "LB", position_zh: "左后卫"},
      {number: 17, name: "Lukáš Sadílek", name_zh: "萨迪莱克", position: "CDM", position_zh: "后腰"},
      {number: 18, name: "David Jurásek", name_zh: "尤拉塞克", position: "LB", position_zh: "左后卫"},
      {number: 19, name: "Martin Vitík", name_zh: "维蒂克", position: "CB", position_zh: "中后卫"},
      {number: 20, name: "Aleš Mandous", name_zh: "曼杜斯", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WDWLWWLDWW", goals_scored_last10: 14, goals_conceded_last10: 10
  },
  {
    code: "BIH", name: "Bosnia and Herzegovina", name_zh: "波黑", group: "B", flag_emoji: "🇧🇦",
    elo_rating: 1680, fifa_rank: 45, confederation: "UEFA", formation: "4-2-3-1",
    key_players: [
      {name: "Edin Džeko", position: "ST"},
      {name: "Miralem Pjanić", position: "CM"},
      {name: "Rade Krunić", position: "CAM"},
      {name: "Sead Kolašinac", position: "LB"},
      {name: "Anel Ahmedhodžić", position: "CB"}
    ],
    squad: [
      {number: 1, name: "Asmir Begović", name_zh: "贝戈维奇", position: "GK", position_zh: "门将"},
      {number: 2, name: "Anel Ahmedhodžić", name_zh: "艾哈迈德霍季奇", position: "CB", position_zh: "中后卫"},
      {number: 3, name: "Sead Kolašinac", name_zh: "科拉希纳茨", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Jusuf Gazibegović", name_zh: "加齐贝戈维奇", position: "RB", position_zh: "右后卫"},
      {number: 5, name: "Nikola Katić", name_zh: "卡蒂奇", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Miralem Pjanić", name_zh: "皮亚尼奇", position: "CM", position_zh: "中前卫"},
      {number: 7, name: "Rade Krunić", name_zh: "克鲁尼奇", position: "CAM", position_zh: "前腰"},
      {number: 8, name: "Samed Baždarević", name_zh: "巴日达雷维奇", position: "CDM", position_zh: "后腰"},
      {number: 9, name: "Edin Džeko", name_zh: "哲科", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Armin Hodžić", name_zh: "霍季奇", position: "ST", position_zh: "前锋"},
      {number: 11, name: "Luka Menalo", name_zh: "梅纳洛", position: "RW", position_zh: "右边锋"},
      {number: 12, name: "Nikola Vasilj", name_zh: "瓦西利", position: "GK", position_zh: "门将"},
      {number: 13, name: "Amar Dedić", name_zh: "德迪奇", position: "RB", position_zh: "右后卫"},
      {number: 14, name: "Sandro Kulenović", name_zh: "库莱诺维奇", position: "ST", position_zh: "前锋"},
      {number: 15, name: "Gojko Cimirot", name_zh: "齐米罗特", position: "CDM", position_zh: "后腰"},
      {number: 16, name: "Haris Hajradinović", name_zh: "哈伊拉迪诺维奇", position: "LW", position_zh: "左边锋"},
      {number: 17, name: "Eldar Ćivić", name_zh: "齐维奇", position: "LB", position_zh: "左后卫"},
      {number: 18, name: "Deni Milošević", name_zh: "米洛舍维奇", position: "CM", position_zh: "中前卫"},
      {number: 19, name: "Stjepan Radeljić", name_zh: "拉德尔吉奇", position: "CB", position_zh: "中后卫"},
      {number: 20, name: "Ibrahim Šehić", name_zh: "谢希奇", position: "GK", position_zh: "门将"}
    ],
    recent_form: "LWDLWLLWDL", goals_scored_last10: 12, goals_conceded_last10: 14
  },
  {
    code: "HAI", name: "Haiti", name_zh: "海地", group: "C", flag_emoji: "🇭🇹",
    elo_rating: 1550, fifa_rank: 65, confederation: "CONCACAF", formation: "4-4-2",
    key_players: [
      {name: "Duckens Nazon", position: "ST"},
      {name: "Frantzdy Pierrot", position: "ST"},
      {name: "Bryan Alceus", position: "CM"},
      {name: "Wilde-Donald Gérier", position: "CDM"},
      {name: "Jean-Kevin Duverne", position: "RB"}
    ],
    squad: [
      {number: 1, name: "Johny Placide", name_zh: "普拉西德", position: "GK", position_zh: "门将"},
      {number: 2, name: "Jean-Kevin Duverne", name_zh: "杜韦尔纳", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "Audy Gédéon", name_zh: "格德翁", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Ricardo Ade", name_zh: "阿德", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Fabrice Noël", name_zh: "诺埃尔", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Wilde-Donald Gérier", name_zh: "热里耶", position: "CDM", position_zh: "后腰"},
      {number: 7, name: "Bryan Alceus", name_zh: "阿尔修斯", position: "CM", position_zh: "中前卫"},
      {number: 8, name: "Hervé Bazile", name_zh: "巴齐尔", position: "CAM", position_zh: "前腰"},
      {number: 9, name: "Duckens Nazon", name_zh: "纳松", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Frantzdy Pierrot", name_zh: "皮埃罗", position: "ST", position_zh: "前锋"},
      {number: 11, name: "Jeff Louis", name_zh: "杰夫·路易", position: "LW", position_zh: "左边锋"},
      {number: 12, name: "Josué Duverger", name_zh: "杜韦尔热", position: "GK", position_zh: "门将"},
      {number: 13, name: "Kevin Lafrance", name_zh: "拉弗朗斯", position: "CM", position_zh: "中前卫"},
      {number: 14, name: "Carnejy Antoine", name_zh: "安托万", position: "RW", position_zh: "右边锋"},
      {number: 15, name: "Mechack Jérôme", name_zh: "热罗姆", position: "CB", position_zh: "中后卫"},
      {number: 16, name: "Steeve Sainristil", name_zh: "森里斯蒂尔", position: "LB", position_zh: "左后卫"},
      {number: 17, name: "Emmanuel Sanon", name_zh: "萨农", position: "CM", position_zh: "中前卫"},
      {number: 18, name: "Bertin Lainé", name_zh: "莱内", position: "CDM", position_zh: "后腰"},
      {number: 19, name: "Djimy Alexis", name_zh: "亚历克西", position: "CB", position_zh: "中后卫"},
      {number: 20, name: "Alan Juste", name_zh: "朱斯特", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WLLDWLDWLL", goals_scored_last10: 9, goals_conceded_last10: 15
  },
  {
    code: "SCO", name: "Scotland", name_zh: "苏格兰", group: "C", flag_emoji: "🏴",
    elo_rating: 1700, fifa_rank: 38, confederation: "UEFA", formation: "4-3-3",
    key_players: [
      {name: "Scott McTominay", position: "CM"},
      {name: "Andrew Robertson", position: "LB"},
      {name: "John McGinn", position: "CM"},
      {name: "Lyndon Dykes", position: "ST"},
      {name: "Kieran Tierney", position: "CB"}
    ],
    squad: [
      {number: 1, name: "Angus Gunn", name_zh: "安格斯·冈恩", position: "GK", position_zh: "门将"},
      {number: 2, name: "Aaron Hickey", name_zh: "希基", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "Andrew Robertson", name_zh: "罗伯逊", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Kieran Tierney", name_zh: "蒂尔尼", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Grant Hanley", name_zh: "汉利", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Scott McTominay", name_zh: "麦克托米奈", position: "CM", position_zh: "中前卫"},
      {number: 7, name: "John McGinn", name_zh: "麦金", position: "CM", position_zh: "中前卫"},
      {number: 8, name: "Callum McGregor", name_zh: "卡勒姆·麦格雷戈", position: "CM", position_zh: "中前卫"},
      {number: 9, name: "Lyndon Dykes", name_zh: "戴克斯", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Che Adams", name_zh: "亚当斯", position: "ST", position_zh: "前锋"},
      {number: 11, name: "Stuart Armstrong", name_zh: "阿姆斯特朗", position: "CAM", position_zh: "前腰"},
      {number: 12, name: "Zander Clark", name_zh: "克拉克", position: "GK", position_zh: "门将"},
      {number: 13, name: "Ryan Porteous", name_zh: "波尔蒂斯", position: "CB", position_zh: "中后卫"},
      {number: 14, name: "Lewis Ferguson", name_zh: "刘易斯·弗格森", position: "CAM", position_zh: "前腰"},
      {number: 15, name: "Nathan Patterson", name_zh: "帕特森", position: "RB", position_zh: "右后卫"},
      {number: 16, name: "Billy Gilmour", name_zh: "吉尔莫", position: "CM", position_zh: "中前卫"},
      {number: 17, name: "Jacob Brown", name_zh: "雅各布·布朗", position: "RW", position_zh: "右边锋"},
      {number: 18, name: "Kenny McLean", name_zh: "麦克莱恩", position: "CDM", position_zh: "后腰"},
      {number: 19, name: "Jack Hendry", name_zh: "亨德里", position: "CB", position_zh: "中后卫"},
      {number: 20, name: "Liam Kelly", name_zh: "凯利", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WDLLWDLWDL", goals_scored_last10: 11, goals_conceded_last10: 14
  },
  {
    code: "PAR", name: "Paraguay", name_zh: "巴拉圭", group: "D", flag_emoji: "🇵🇾",
    elo_rating: 1690, fifa_rank: 42, confederation: "CONMEBOL", formation: "4-3-3",
    key_players: [
      {name: "Miguel Almirón", position: "RW"},
      {name: "Antonín Barrios", position: "CAM"},
      {name: "Omar Alderete", position: "CB"},
      {name: "Gustavo Gómez", position: "CB"},
      {name: "Ángel Romero", position: "ST"}
    ],
    squad: [
      {number: 1, name: "Anthony Silva", name_zh: "席尔瓦", position: "GK", position_zh: "门将"},
      {number: 2, name: "Robert Rojas", name_zh: "罗哈斯", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "Mathías Villasanti", name_zh: "比利亚桑蒂", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Omar Alderete", name_zh: "阿尔德雷特", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Gustavo Gómez", name_zh: "古斯塔沃·戈麦斯", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Andrés Cubas", name_zh: "库瓦斯", position: "CDM", position_zh: "后腰"},
      {number: 7, name: "Antonín Barrios", name_zh: "巴里奥斯", position: "CAM", position_zh: "前腰"},
      {number: 8, name: "Hernesto Caballero", name_zh: "卡瓦列罗", position: "CM", position_zh: "中前卫"},
      {number: 9, name: "Ángel Romero", name_zh: "罗梅罗", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Miguel Almirón", name_zh: "阿尔米隆", position: "RW", position_zh: "右边锋"},
      {number: 11, name: "Julio Enciso", name_zh: "恩西索", position: "LW", position_zh: "左边锋"},
      {number: 12, name: "Alfredo Aguilar", name_zh: "阿吉拉尔", position: "GK", position_zh: "门将"},
      {number: 13, name: "Fabián Balbuena", name_zh: "巴尔布埃纳", position: "CB", position_zh: "中后卫"},
      {number: 14, name: "Alejandro Romero Gamarra", name_zh: "罗梅罗·加马拉", position: "CM", position_zh: "中前卫"},
      {number: 15, name: "Adam Bareiro", name_zh: "巴雷罗", position: "ST", position_zh: "前锋"},
      {number: 16, name: "Iván Ramírez", name_zh: "拉米雷斯", position: "RB", position_zh: "右后卫"},
      {number: 17, name: "Sergio Peña", name_zh: "佩尼亚", position: "CM", position_zh: "中前卫"},
      {number: 18, name: "Jorge Morel", name_zh: "莫雷尔", position: "CB", position_zh: "中后卫"},
      {number: 19, name: "Derlis González", name_zh: "德利斯·冈萨雷斯", position: "LW", position_zh: "左边锋"},
      {number: 20, name: "Gatito Fernández", name_zh: "费尔南德斯", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WDWLDLWWDL", goals_scored_last10: 11, goals_conceded_last10: 12
  },
  {
    code: "TUR", name: "Turkey", name_zh: "土耳其", group: "D", flag_emoji: "🇹🇷",
    elo_rating: 1740, fifa_rank: 28, confederation: "UEFA", formation: "4-2-3-1",
    key_players: [
      {name: "Hakan Çalhanoğlu", position: "CM"},
      {name: "Arda Güler", position: "CAM"},
      {name: "Cengiz Ünder", position: "RW"},
      {name: "Merih Demiral", position: "CB"},
      {name: "Ferdi Kadıoğlu", position: "LB"}
    ],
    squad: [
      {number: 1, name: "Mert Günok", name_zh: "居诺克", position: "GK", position_zh: "门将"},
      {number: 2, name: "Zeki Çelik", name_zh: "泽基·切利克", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "Ferdi Kadıoğlu", name_zh: "费尔迪·卡迪奥卢", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Merih Demiral", name_zh: "德米拉尔", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Abdülkerim Bardakcı", name_zh: "巴尔德克哲", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Hakan Çalhanoğlu", name_zh: "恰尔汗奥卢", position: "CM", position_zh: "中前卫"},
      {number: 7, name: "Arda Güler", name_zh: "居莱尔", position: "CAM", position_zh: "前腰"},
      {number: 8, name: "İrfan Can Kahveci", name_zh: "卡赫韦吉", position: "CM", position_zh: "中前卫"},
      {number: 9, name: "Cenk Tosun", name_zh: "托松", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Cengiz Ünder", name_zh: "云代尔", position: "RW", position_zh: "右边锋"},
      {number: 11, name: "Kerem Aktürkoğlu", name_zh: "阿克蒂尔科卢", position: "LW", position_zh: "左边锋"},
      {number: 12, name: "Altay Bayındır", name_zh: "巴因德尔", position: "GK", position_zh: "门将"},
      {number: 13, name: "Samet Akaydın", name_zh: "阿卡伊丁", position: "CB", position_zh: "中后卫"},
      {number: 14, name: "Barış Alper Yılmaz", name_zh: "耶尔马兹", position: "LW", position_zh: "左边锋"},
      {number: 15, name: "Orkun Kökçü", name_zh: "科克曲", position: "CM", position_zh: "中前卫"},
      {number: 16, name: "Eren Dinkçi", name_zh: "丁克奇", position: "RW", position_zh: "右边锋"},
      {number: 17, name: "Ozan Kabak", name_zh: "卡巴克", position: "CB", position_zh: "中后卫"},
      {number: 18, name: "Kaan Ayhan", name_zh: "艾汉", position: "CB", position_zh: "中后卫"},
      {number: 19, name: "Enes Ünal", name_zh: "乌纳尔", position: "ST", position_zh: "前锋"},
      {number: 20, name: "Uğurcan Çakır", name_zh: "恰克尔", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WWWDWLWWWD", goals_scored_last10: 19, goals_conceded_last10: 10
  },
  {
    code: "CUW", name: "Curaçao", name_zh: "库拉索", group: "E", flag_emoji: "🇨🇼",
    elo_rating: 1520, fifa_rank: 75, confederation: "CONCACAF", formation: "4-4-2",
    key_players: [
      {name: "Leandro Bacuna", position: "CM"},
      {name: "Juninho Bacuna", position: "CAM"},
      {name: "Cuco Martina", position: "RB"},
      {name: "Brandon Servania", position: "ST"},
      {name: "Juriën Gaari", position: "RB"}
    ],
    squad: [
      {number: 1, name: "Eloy Room", name_zh: "罗姆", position: "GK", position_zh: "门将"},
      {number: 2, name: "Cuco Martina", name_zh: "库科·马丁纳", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "Juriën Gaari", name_zh: "加里", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Denzel Sluis", name_zh: "斯路易斯", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Shanon Carmacia", name_zh: "卡尔马西亚", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Leandro Bacuna", name_zh: "莱安德罗·巴库纳", position: "CM", position_zh: "中前卫"},
      {number: 7, name: "Juninho Bacuna", name_zh: "朱尼尼奥·巴库纳", position: "CAM", position_zh: "前腰"},
      {number: 8, name: "Kenji Gorré", name_zh: "戈雷", position: "CM", position_zh: "中前卫"},
      {number: 9, name: "Brandon Servania", name_zh: "塞尔瓦尼亚", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Rangelo Janga", name_zh: "扬加", position: "ST", position_zh: "前锋"},
      {number: 11, name: "Gaston Brugman", name_zh: "布鲁格曼", position: "CDM", position_zh: "后腰"},
      {number: 12, name: "Tyrone Conraad", name_zh: "康拉德", position: "GK", position_zh: "门将"},
      {number: 13, name: "Daihiro Kogi", name_zh: "科吉", position: "CB", position_zh: "中后卫"},
      {number: 14, name: "Charlton Bernaldo", name_zh: "贝尔纳多", position: "LW", position_zh: "左边锋"},
      {number: 15, name: "Javier Espinosa", name_zh: "埃斯皮诺萨", position: "CM", position_zh: "中前卫"},
      {number: 16, name: "Ramiz Zerrouki", name_zh: "泽鲁基", position: "CDM", position_zh: "后腰"},
      {number: 17, name: "Michael Maria", name_zh: "玛丽亚", position: "LW", position_zh: "左边锋"},
      {number: 18, name: "Gevaro Nepomuceno", name_zh: "内波穆切诺", position: "RW", position_zh: "右边锋"},
      {number: 19, name: "Jerold Promes", name_zh: "普罗梅斯", position: "CB", position_zh: "中后卫"},
      {number: 20, name: "Hector Hevel", name_zh: "赫维尔", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WLDLWWLDWL", goals_scored_last10: 10, goals_conceded_last10: 13
  },
  {
    code: "SWE", name: "Sweden", name_zh: "瑞典", group: "F", flag_emoji: "🇸🇪",
    elo_rating: 1710, fifa_rank: 36, confederation: "UEFA", formation: "4-4-2",
    key_players: [
      {name: "Alexander Isak", position: "ST"},
      {name: "Dejan Kulusevski", position: "RW"},
      {name: "Emil Forsberg", position: "CAM"},
      {name: "Victor Lindelöf", position: "CB"},
      {name: "Robin Olsen", position: "GK"}
    ],
    squad: [
      {number: 1, name: "Robin Olsen", name_zh: "奥尔森", position: "GK", position_zh: "门将"},
      {number: 2, name: "Emil Krafth", name_zh: "克拉夫特", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "Victor Lindelöf", name_zh: "林德勒夫", position: "CB", position_zh: "中后卫"},
      {number: 4, name: "Isak Hien", name_zh: "希恩", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Ludwig Augustinsson", name_zh: "奥古斯丁松", position: "LB", position_zh: "左后卫"},
      {number: 6, name: "Sebastian Larsson", name_zh: "拉尔森", position: "CM", position_zh: "中前卫"},
      {number: 7, name: "Dejan Kulusevski", name_zh: "库卢塞夫斯基", position: "RW", position_zh: "右边锋"},
      {number: 8, name: "Emil Forsberg", name_zh: "福斯贝里", position: "CAM", position_zh: "前腰"},
      {number: 9, name: "Alexander Isak", name_zh: "伊萨克", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Viktor Gyökeres", name_zh: "约克雷斯", position: "ST", position_zh: "前锋"},
      {number: 11, name: "Anthony Elanga", name_zh: "埃兰加", position: "LW", position_zh: "左边锋"},
      {number: 12, name: "Karl-Johan Johnsson", name_zh: "约翰松", position: "GK", position_zh: "门将"},
      {number: 13, name: "Pontus Jansson", name_zh: "扬松", position: "CB", position_zh: "中后卫"},
      {number: 14, name: "Hugo Larsson", name_zh: "雨果·拉尔森", position: "CM", position_zh: "中前卫"},
      {number: 15, name: "Ken Sema", name_zh: "塞马", position: "LW", position_zh: "左边锋"},
      {number: 16, name: "Jesper Karlström", name_zh: "卡尔斯特伦", position: "CDM", position_zh: "后腰"},
      {number: 17, name: "Natanael Elnegaard", name_zh: "埃内加德", position: "RB", position_zh: "右后卫"},
      {number: 18, name: "Mattias Svanberg", name_zh: "斯万贝里", position: "CM", position_zh: "中前卫"},
      {number: 19, name: "Joakim Nilsson", name_zh: "尼尔松", position: "CB", position_zh: "中后卫"},
      {number: 20, name: "Kristoffer Nordfeldt", name_zh: "诺德费尔特", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WWDWLWLDWW", goals_scored_last10: 15, goals_conceded_last10: 10
  },
  {
    code: "TUN", name: "Tunisia", name_zh: "突尼斯", group: "F", flag_emoji: "🇹🇳",
    elo_rating: 1670, fifa_rank: 48, confederation: "CAF", formation: "4-3-3",
    key_players: [
      {name: "Youssef Msakni", position: "LW"},
      {name: "Wahbi Khazri", position: "ST"},
      {name: "Ellyes Skhiri", position: "CDM"},
      {name: "Ali Maâloul", position: "LB"},
      {name: "Dylan Bronn", position: "CB"}
    ],
    squad: [
      {number: 1, name: "Aymen Dahmen", name_zh: "达门", position: "GK", position_zh: "门将"},
      {number: 2, name: "Ali Maâloul", name_zh: "马卢勒", position: "LB", position_zh: "左后卫"},
      {number: 3, name: "Dylan Bronn", name_zh: "布龙", position: "CB", position_zh: "中后卫"},
      {number: 4, name: "Montassar Talbi", name_zh: "塔尔比", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Nader Ghandri", name_zh: "甘德里", position: "RB", position_zh: "右后卫"},
      {number: 6, name: "Ellyes Skhiri", name_zh: "斯希里", position: "CDM", position_zh: "后腰"},
      {number: 7, name: "Ferjani Sassi", name_zh: "萨西", position: "CM", position_zh: "中前卫"},
      {number: 8, name: "Hannibal Mejbri", name_zh: "梅布里", position: "CAM", position_zh: "前腰"},
      {number: 9, name: "Wahbi Khazri", name_zh: "哈兹里", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Youssef Msakni", name_zh: "姆萨克尼", position: "LW", position_zh: "左边锋"},
      {number: 11, name: "Naïm Sliti", name_zh: "斯利蒂", position: "RW", position_zh: "右边锋"},
      {number: 12, name: "Moez Ben Cherifia", name_zh: "本·谢里菲亚", position: "GK", position_zh: "门将"},
      {number: 13, name: "Anis Ben Slimane", name_zh: "本·斯利曼", position: "CM", position_zh: "中前卫"},
      {number: 14, name: "Issam Jebali", name_zh: "杰巴利", position: "ST", position_zh: "前锋"},
      {number: 15, name: "Mehdi Leye", name_zh: "莱耶", position: "CB", position_zh: "中后卫"},
      {number: 16, name: "Amine Ben Rejeb", name_zh: "本·雷杰布", position: "RB", position_zh: "右后卫"},
      {number: 17, name: "Ghaylen Chaalel", name_zh: "沙阿莱勒", position: "CM", position_zh: "中前卫"},
      {number: 18, name: "Seifeddine Jaziri", name_zh: "贾齐里", position: "ST", position_zh: "前锋"},
      {number: 19, name: "Bilel Ifa", name_zh: "伊法", position: "CB", position_zh: "中后卫"},
      {number: 20, name: "Farouk Ben Mustapha", name_zh: "本·穆斯塔法", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WDWLWWLDWL", goals_scored_last10: 12, goals_conceded_last10: 11
  },
  {
    code: "NZL", name: "New Zealand", name_zh: "新西兰", group: "G", flag_emoji: "🇳🇿",
    elo_rating: 1580, fifa_rank: 60, confederation: "OFC", formation: "4-4-2",
    key_players: [
      {name: "Chris Wood", position: "ST"},
      {name: "Winston Reid", position: "CB"},
      {name: "Ryan Thomas", position: "CM"},
      {name: "Marco Rojas", position: "RW"},
      {name: "Liberato Cacace", position: "LB"}
    ],
    squad: [
      {number: 1, name: "Stefan Marinovic", name_zh: "马里诺维奇", position: "GK", position_zh: "门将"},
      {number: 2, name: "Liberato Cacace", name_zh: "卡卡切", position: "LB", position_zh: "左后卫"},
      {number: 3, name: "Winston Reid", name_zh: "温斯顿·里德", position: "CB", position_zh: "中后卫"},
      {number: 4, name: "Tommy Smith", name_zh: "汤米·史密斯", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Nando Pijnaker", name_zh: "派纳克", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Ryan Thomas", name_zh: "瑞安·托马斯", position: "CM", position_zh: "中前卫"},
      {number: 7, name: "Marco Rojas", name_zh: "罗哈斯", position: "RW", position_zh: "右边锋"},
      {number: 8, name: "Joe Champness", name_zh: "钱普尼斯", position: "CAM", position_zh: "前腰"},
      {number: 9, name: "Chris Wood", name_zh: "克里斯·伍德", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Sarpreet Singh", name_zh: "辛格", position: "LW", position_zh: "左边锋"},
      {number: 11, name: "Kosta Barbarouses", name_zh: "巴巴鲁塞斯", position: "RW", position_zh: "右边锋"},
      {number: 12, name: "Oliver Sail", name_zh: "塞尔", position: "GK", position_zh: "门将"},
      {number: 13, name: "Michael Boxall", name_zh: "博克索尔", position: "CB", position_zh: "中后卫"},
      {number: 14, name: "Callum McCowatt", name_zh: "麦科瓦特", position: "LW", position_zh: "左边锋"},
      {number: 15, name: "Clayton Lewis", name_zh: "克莱顿·刘易斯", position: "CM", position_zh: "中前卫"},
      {number: 16, name: "Deklan Wynne", name_zh: "温内", position: "RB", position_zh: "右后卫"},
      {number: 17, name: "Elijah Just", name_zh: "贾斯特", position: "CM", position_zh: "中前卫"},
      {number: 18, name: "Ben Waine", name_zh: "韦恩", position: "ST", position_zh: "前锋"},
      {number: 19, name: "Tyler Boyd", name_zh: "博伊德", position: "LW", position_zh: "左边锋"},
      {number: 20, name: "Glen Moss", name_zh: "莫斯", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WWDWLLWWDL", goals_scored_last10: 14, goals_conceded_last10: 10
  },
  {
    code: "CPV", name: "Cape Verde", name_zh: "佛得角", group: "H", flag_emoji: "🇨🇻",
    elo_rating: 1630, fifa_rank: 52, confederation: "CAF", formation: "4-3-3",
    key_players: [
      {name: "Ryan Mendes", position: "LW"},
      {name: "Garry Rodrigues", position: "RW"},
      {name: "Steven Fortes", position: "CB"},
      {name: "Lisandro Semedo", position: "ST"},
      {name: "Vozinha", position: "GK"}
    ],
    squad: [
      {number: 1, name: "Vozinha", name_zh: "沃齐尼亚", position: "GK", position_zh: "门将"},
      {number: 2, name: "Steven Fortes", name_zh: "福尔特斯", position: "CB", position_zh: "中后卫"},
      {number: 3, name: "Diney Borges", name_zh: "博尔热斯", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Roberto Lopes", name_zh: "洛佩斯", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Kenny Rocha Santos", name_zh: "桑托斯", position: "RB", position_zh: "右后卫"},
      {number: 6, name: "Willyan Rocha", name_zh: "威利安·罗查", position: "CDM", position_zh: "后腰"},
      {number: 7, name: "Ryan Mendes", name_zh: "瑞安·门德斯", position: "LW", position_zh: "左边锋"},
      {number: 8, name: "Jamiro Monteiro", name_zh: "蒙泰罗", position: "CM", position_zh: "中前卫"},
      {number: 9, name: "Lisandro Semedo", name_zh: "塞梅多", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Garry Rodrigues", name_zh: "加里·罗德里格斯", position: "RW", position_zh: "右边锋"},
      {number: 11, name: "Júlio Tavares", name_zh: "塔瓦雷斯", position: "ST", position_zh: "前锋"},
      {number: 12, name: "Marcio da Rosa", name_zh: "达罗萨", position: "GK", position_zh: "门将"},
      {number: 13, name: "Ivanildo Rozenblad", name_zh: "罗森布拉德", position: "CB", position_zh: "中后卫"},
      {number: 14, name: "Fábio Cardoso", name_zh: "卡多索", position: "CM", position_zh: "中前卫"},
      {number: 15, name: "Derick Poloni", name_zh: "波洛尼", position: "RB", position_zh: "右后卫"},
      {number: 16, name: "Patrick Andrade", name_zh: "安德拉德", position: "CDM", position_zh: "后腰"},
      {number: 17, name: "Edi Semedo", name_zh: "埃迪·塞梅多", position: "LW", position_zh: "左边锋"},
      {number: 18, name: "Zé Luís", name_zh: "泽·路易斯", position: "ST", position_zh: "前锋"},
      {number: 19, name: "Carlos Andrade", name_zh: "卡洛斯·安德拉德", position: "CB", position_zh: "中后卫"},
      {number: 20, name: "Elber Evora", name_zh: "埃沃拉", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WWDWLWWLDW", goals_scored_last10: 13, goals_conceded_last10: 10
  },
  {
    code: "IRQ", name: "Iraq", name_zh: "伊拉克", group: "I", flag_emoji: "🇮🇶",
    elo_rating: 1600, fifa_rank: 58, confederation: "AFC", formation: "4-2-3-1",
    key_players: [
      {name: "Ayman Hussein", position: "ST"},
      {name: "Aymen Hussein", position: "ST"},
      {name: "Ali Adnan", position: "LB"},
      {name: "Safaa Hadi", position: "CM"},
      {name: "Ibrahim Bayesh", position: "RW"}
    ],
    squad: [
      {number: 1, name: "Jalal Hassan", name_zh: "贾拉勒·哈桑", position: "GK", position_zh: "门将"},
      {number: 2, name: "Ahmed Yasin", name_zh: "艾哈迈德·亚辛", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "Ali Adnan", name_zh: "阿里·阿德南", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Saad Natiq", name_zh: "萨阿德·纳蒂克", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Bashar Resan", name_zh: "巴沙尔·雷桑", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Safaa Hadi", name_zh: "萨法·哈迪", position: "CDM", position_zh: "后腰"},
      {number: 7, name: "Ibrahim Bayesh", name_zh: "伊布拉欣·巴耶什", position: "RW", position_zh: "右边锋"},
      {number: 8, name: "Amjad Atwan", name_zh: "阿姆贾德·阿特万", position: "CM", position_zh: "中前卫"},
      {number: 9, name: "Ayman Hussein", name_zh: "艾曼·侯赛因", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Mohannad Ali", name_zh: "穆汉纳德·阿里", position: "CAM", position_zh: "前腰"},
      {number: 11, name: "Hussein Ali", name_zh: "侯赛因·阿里", position: "LW", position_zh: "左边锋"},
      {number: 12, name: "Mohammed Hameed", name_zh: "穆罕默德·哈米德", position: "GK", position_zh: "门将"},
      {number: 13, name: "Zidane Iqbal", name_zh: "齐达内·伊克巴尔", position: "CM", position_zh: "中前卫"},
      {number: 14, name: "Alaa Abbas", name_zh: "阿拉·阿巴斯", position: "ST", position_zh: "前锋"},
      {number: 15, name: "Rebin Solaka", name_zh: "雷宾·索拉卡", position: "CB", position_zh: "中后卫"},
      {number: 16, name: "Muntadher Mohammed", name_zh: "蒙塔德尔·穆罕默德", position: "CB", position_zh: "中后卫"},
      {number: 17, name: "Ali Jasim", name_zh: "阿里·贾西姆", position: "LW", position_zh: "左边锋"},
      {number: 18, name: "Akram Hashim", name_zh: "阿克拉姆·哈希姆", position: "RB", position_zh: "右后卫"},
      {number: 19, name: "Dhurgham Ismail", name_zh: "杜尔加姆·伊斯梅尔", position: "LB", position_zh: "左后卫"},
      {number: 20, name: "Ahmed Basil", name_zh: "艾哈迈德·巴塞尔", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WLDWWLDWWL", goals_scored_last10: 13, goals_conceded_last10: 11
  },
  {
    code: "NOR", name: "Norway", name_zh: "挪威", group: "I", flag_emoji: "🇳🇴",
    elo_rating: 1730, fifa_rank: 30, confederation: "UEFA", formation: "4-3-3",
    key_players: [
      {name: "Erling Haaland", position: "ST"},
      {name: "Martin Ødegaard", position: "CAM"},
      {name: "Sander Berge", position: "CM"},
      {name: "Raphaël Varane", position: "CB"},
      {name: "David Raya", position: "GK"}
    ],
    squad: [
      {number: 1, name: "Karl-Johan Johnsson", name_zh: "约翰松", position: "GK", position_zh: "门将"},
      {number: 2, name: "Julian Ryerson", name_zh: "赖尔松", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "Birger Meling", name_zh: "梅林", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Leo Østigård", name_zh: "厄斯蒂高", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Stefan Strandberg", name_zh: "斯特兰德贝里", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Sander Berge", name_zh: "桑德尔·贝格", position: "CM", position_zh: "中前卫"},
      {number: 7, name: "Martin Ødegaard", name_zh: "厄德高", position: "CAM", position_zh: "前腰"},
      {number: 8, name: "Mats Møller Dæhli", name_zh: "代利", position: "CM", position_zh: "中前卫"},
      {number: 9, name: "Erling Haaland", name_zh: "哈兰德", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Alexander Sørloth", name_zh: "索尔洛特", position: "ST", position_zh: "前锋"},
      {number: 11, name: "Oda Malin Eriksen", name_zh: "埃里克森", position: "RW", position_zh: "右边锋"},
      {number: 12, name: "André Hansen", name_zh: "汉森", position: "GK", position_zh: "门将"},
      {number: 13, name: "Kristoffer Ajer", name_zh: "阿耶尔", position: "CB", position_zh: "中后卫"},
      {number: 14, name: "Fredrik Aursnes", name_zh: "奥尔斯内斯", position: "CM", position_zh: "中前卫"},
      {number: 15, name: "Mohamed Elyounoussi", name_zh: "埃尔尤努西", position: "LW", position_zh: "左边锋"},
      {number: 16, name: "Patrick Berg", name_zh: "贝格", position: "CDM", position_zh: "后腰"},
      {number: 17, name: "Antonio Nusa", name_zh: "努萨", position: "RW", position_zh: "右边锋"},
      {number: 18, name: "Morten Thorsby", name_zh: "托尔斯比", position: "CM", position_zh: "中前卫"},
      {number: 19, name: "Oscar Bobb", name_zh: "博布", position: "RW", position_zh: "右边锋"},
      {number: 20, name: "Egil Selvik", name_zh: "塞尔维克", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WWWWDLWWWW", goals_scored_last10: 24, goals_conceded_last10: 6
  },
  {
    code: "ALG", name: "Algeria", name_zh: "阿尔及利亚", group: "J", flag_emoji: "🇩🇿",
    elo_rating: 1660, fifa_rank: 50, confederation: "CAF", formation: "4-2-3-1",
    key_players: [
      {name: "Riyad Mahrez", position: "RW"},
      {name: "Ismaël Bennacer", position: "CM"},
      {name: "Sofiane Feghouli", position: "CAM"},
      {name: "Aïssa Mandi", position: "RB"},
      {name: "Islam Slimani", position: "ST"}
    ],
    squad: [
      {number: 1, name: "Rais M'Bolhi", name_zh: "姆博利", position: "GK", position_zh: "门将"},
      {number: 2, name: "Aïssa Mandi", name_zh: "曼迪", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "Ramy Bensebaini", name_zh: "本塞拜尼", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Djamel Benlamri", name_zh: "本拉姆里", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Aïmen Moueffek", name_zh: "穆埃菲克", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Ismaël Bennacer", name_zh: "本纳塞尔", position: "CM", position_zh: "中前卫"},
      {number: 7, name: "Sofiane Feghouli", name_zh: "费古利", position: "CAM", position_zh: "前腰"},
      {number: 8, name: "Adlène Guedioura", name_zh: "盖迪奥拉", position: "CDM", position_zh: "后腰"},
      {number: 9, name: "Islam Slimani", name_zh: "斯利马尼", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Riyad Mahrez", name_zh: "马赫雷斯", position: "RW", position_zh: "右边锋"},
      {number: 11, name: "Yacine Brahimi", name_zh: "卜拉希米", position: "LW", position_zh: "左边锋"},
      {number: 12, name: "Alexandre Oukidja", name_zh: "乌基贾", position: "GK", position_zh: "门将"},
      {number: 13, name: "Hicham Boudaoui", name_zh: "布达维", position: "CM", position_zh: "中前卫"},
      {number: 14, name: "Adam Ounas", name_zh: "乌纳斯", position: "LW", position_zh: "左边锋"},
      {number: 15, name: "Mehdi Tahrat", name_zh: "塔赫拉特", position: "CB", position_zh: "中后卫"},
      {number: 16, name: "Sofiane Hanitser", name_zh: "哈尼特塞尔", position: "CDM", position_zh: "后腰"},
      {number: 17, name: "Farid Boulaya", name_zh: "布拉亚", position: "CAM", position_zh: "前腰"},
      {number: 18, name: "Mohamed Amine Amoura", name_zh: "阿穆拉", position: "ST", position_zh: "前锋"},
      {number: 19, name: "Rafik Guitane", name_zh: "吉坦", position: "CM", position_zh: "中前卫"},
      {number: 20, name: "Moustapha Zeghba", name_zh: "泽格巴", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WDWWLLWDWW", goals_scored_last10: 14, goals_conceded_last10: 10
  },
  {
    code: "AUT", name: "Austria", name_zh: "奥地利", group: "J", flag_emoji: "🇦🇹",
    elo_rating: 1750, fifa_rank: 26, confederation: "UEFA", formation: "4-2-3-1",
    key_players: [
      {name: "David Alaba", position: "CB"},
      {name: "Marcel Sabitzer", position: "CM"},
      {name: "Konrad Laimer", position: "RB"},
      {name: "Marko Arnautović", position: "ST"},
      {name: "Xaver Schlager", position: "CDM"}
    ],
    squad: [
      {number: 1, name: "Heinz Lindner", name_zh: "林德纳", position: "GK", position_zh: "门将"},
      {number: 2, name: "Konrad Laimer", name_zh: "莱默尔", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "David Alaba", name_zh: "阿拉巴", position: "CB", position_zh: "中后卫"},
      {number: 4, name: "Kevin Danso", name_zh: "丹索", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Maximilian Wöber", name_zh: "韦贝尔", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Xaver Schlager", name_zh: "施拉格尔", position: "CDM", position_zh: "后腰"},
      {number: 7, name: "Marcel Sabitzer", name_zh: "萨比策", position: "CM", position_zh: "中前卫"},
      {number: 8, name: "Florian Kainz", name_zh: "凯因茨", position: "LW", position_zh: "左边锋"},
      {number: 9, name: "Marko Arnautović", name_zh: "阿瑙托维奇", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Christoph Baumgartner", name_zh: "鲍姆加特纳", position: "CAM", position_zh: "前腰"},
      {number: 11, name: "Michael Gregoritsch", name_zh: "格雷戈里奇", position: "ST", position_zh: "前锋"},
      {number: 12, name: "Pentz", name_zh: "彭茨", position: "GK", position_zh: "门将"},
      {number: 13, name: "Stefan Posch", name_zh: "波施", position: "CB", position_zh: "中后卫"},
      {number: 14, name: "Stefan Lainer", name_zh: "莱纳", position: "RB", position_zh: "右后卫"},
      {number: 15, name: "Philipp Lienhart", name_zh: "林哈特", position: "CB", position_zh: "中后卫"},
      {number: 16, name: "Nicolas Seiwald", name_zh: "赛瓦尔德", position: "CM", position_zh: "中前卫"},
      {number: 17, name: "Andreas Ulmer", name_zh: "乌尔默", position: "LB", position_zh: "左后卫"},
      {number: 18, name: "Sasa Kalajdzic", name_zh: "卡拉季奇", position: "ST", position_zh: "前锋"},
      {number: 19, name: "Muhammad Cham", name_zh: "查姆", position: "CAM", position_zh: "前腰"},
      {number: 20, name: "Patrick Pentz", name_zh: "帕特里克·彭茨", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WWWWDWLWWW", goals_scored_last10: 20, goals_conceded_last10: 8
  },
  {
    code: "JOR", name: "Jordan", name_zh: "约旦", group: "J", flag_emoji: "🇯🇴",
    elo_rating: 1590, fifa_rank: 62, confederation: "AFC", formation: "4-4-2",
    key_players: [
      {name: "Mousa Al-Tamari", position: "RW"},
      {name: "Yazan Al-Naimat", position: "ST"},
      {name: "Noor Al-Rawabdeh", position: "CM"},
      {name: "Ali Olwan", position: "LW"},
      {name: "Yazan Al-Arab", position: "CB"}
    ],
    squad: [
      {number: 1, name: "Yazid Abulaila", name_zh: "阿布莱拉", position: "GK", position_zh: "门将"},
      {number: 2, name: "Yazan Al-Arab", name_zh: "亚赞·阿拉布", position: "CB", position_zh: "中后卫"},
      {number: 3, name: "Abdallah Nasib", name_zh: "纳斯布", position: "CB", position_zh: "中后卫"},
      {number: 4, name: "Ihsan Haddad", name_zh: "哈达德", position: "RB", position_zh: "右后卫"},
      {number: 5, name: "Mohammad Al-Dmeiri", name_zh: "德迈里", position: "LB", position_zh: "左后卫"},
      {number: 6, name: "Noor Al-Rawabdeh", name_zh: "努尔·拉瓦布德", position: "CM", position_zh: "中前卫"},
      {number: 7, name: "Mousa Al-Tamari", name_zh: "穆萨·塔马里", position: "RW", position_zh: "右边锋"},
      {number: 8, name: "Ahmed Samir", name_zh: "艾哈迈德·萨米尔", position: "CDM", position_zh: "后腰"},
      {number: 9, name: "Yazan Al-Naimat", name_zh: "亚赞·奈马特", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Ali Olwan", name_zh: "奥勒万", position: "LW", position_zh: "左边锋"},
      {number: 11, name: "Mahmoud Al-Mardi", name_zh: "马尔迪", position: "CAM", position_zh: "前腰"},
      {number: 12, name: "Ahmad Al-Jasim", name_zh: "贾西姆", position: "GK", position_zh: "门将"},
      {number: 13, name: "Anas Al-Awadat", name_zh: "阿瓦达特", position: "CM", position_zh: "中前卫"},
      {number: 14, name: "Nizar Al-Rashdan", name_zh: "拉什丹", position: "CM", position_zh: "中前卫"},
      {number: 15, name: "Salem Al-Ajalin", name_zh: "阿贾林", position: "CB", position_zh: "中后卫"},
      {number: 16, name: "Hamza Al-Dardour", name_zh: "达杜尔", position: "ST", position_zh: "前锋"},
      {number: 17, name: "Rashed Al-Toum", name_zh: "图姆", position: "LW", position_zh: "左边锋"},
      {number: 18, name: "Fadi Al-Awadat", name_zh: "法迪·阿瓦达特", position: "RB", position_zh: "右后卫"},
      {number: 19, name: "Kouka Al-Omari", name_zh: "奥马里", position: "CB", position_zh: "中后卫"},
      {number: 20, name: "Abdulrahman Al-Daajah", name_zh: "达贾", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WWDWWLLDWW", goals_scored_last10: 13, goals_conceded_last10: 10
  },
  {
    code: "COD", name: "DR Congo", name_zh: "刚果(金)", group: "K", flag_emoji: "🇨🇩",
    elo_rating: 1640, fifa_rank: 53, confederation: "CAF", formation: "4-3-3",
    key_players: [
      {name: "Cédric Makiadi", position: "CM"},
      {name: "Dieumerci Mbokani", position: "ST"},
      {name: "Yoane Wissa", position: "LW"},
      {name: "Chancel Mbemba", position: "CB"},
      {name: "Arthur Masuaku", position: "LB"}
    ],
    squad: [
      {number: 1, name: "Lionel Mpasi", name_zh: "姆帕西", position: "GK", position_zh: "门将"},
      {number: 2, name: "Chancel Mbemba", name_zh: "姆本巴", position: "CB", position_zh: "中后卫"},
      {number: 3, name: "Arthur Masuaku", name_zh: "马苏阿库", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Henoc Inonga", name_zh: "因翁加", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Marcel Tisserand", name_zh: "蒂瑟朗", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Samuel Moutoussamy", name_zh: "穆图萨米", position: "CDM", position_zh: "后腰"},
      {number: 7, name: "Yoane Wissa", name_zh: "维萨", position: "LW", position_zh: "左边锋"},
      {number: 8, name: "Gaël Kakuta", name_zh: "卡库塔", position: "CAM", position_zh: "前腰"},
      {number: 9, name: "Dieumerci Mbokani", name_zh: "姆博卡尼", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Cédric Makiadi", name_zh: "马基亚迪", position: "CM", position_zh: "中前卫"},
      {number: 11, name: "Thievy Bifouma", name_zh: "比富马", position: "RW", position_zh: "右边锋"},
      {number: 12, name: "Pascal Kimpembe", name_zh: "金彭贝", position: "GK", position_zh: "门将"},
      {number: 13, name: "Jordan Ikoko", name_zh: "伊科科", position: "RB", position_zh: "右后卫"},
      {number: 14, name: "Neblité Kabanunga", name_zh: "卡巴农加", position: "ST", position_zh: "前锋"},
      {number: 15, name: "Olivier Kemen", name_zh: "凯芒", position: "CM", position_zh: "中前卫"},
      {number: 16, name: "Serge Lino", name_zh: "利诺", position: "CB", position_zh: "中后卫"},
      {number: 17, name: "Firmin Ndombe Mubele", name_zh: "姆贝莱", position: "RW", position_zh: "右边锋"},
      {number: 18, name: "Jackson Muleka", name_zh: "穆莱卡", position: "ST", position_zh: "前锋"},
      {number: 19, name: "Elias Mpele", name_zh: "姆佩莱", position: "LB", position_zh: "左后卫"},
      {number: 20, name: "Vladan Kujović", name_zh: "库约维奇", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WDWLLWWDWL", goals_scored_last10: 13, goals_conceded_last10: 12
  },
  {
    code: "UZB", name: "Uzbekistan", name_zh: "乌兹别克斯坦", group: "K", flag_emoji: "🇺🇿",
    elo_rating: 1610, fifa_rank: 57, confederation: "AFC", formation: "4-2-3-1",
    key_players: [
      {name: "Eldor Shomurodov", position: "ST"},
      {name: "Jaloliddin Masharipov", position: "LW"},
      {name: "Otabek Shukurov", position: "CM"},
      {name: "Abbosbek Fayzullaev", position: "RW"},
      {name: "Egor Krimets", position: "CB"}
    ],
    squad: [
      {number: 1, name: "Utkir Yusupov", name_zh: "尤苏波夫", position: "GK", position_zh: "门将"},
      {number: 2, name: "Egor Krimets", name_zh: "克里梅茨", position: "CB", position_zh: "中后卫"},
      {number: 3, name: "Abror Ismailov", name_zh: "伊斯梅洛夫", position: "CB", position_zh: "中后卫"},
      {number: 4, name: "Khushniddin Parpiev", name_zh: "帕尔皮耶夫", position: "LB", position_zh: "左后卫"},
      {number: 5, name: "Akmal Tursunpulatov", name_zh: "图尔松普拉托夫", position: "RB", position_zh: "右后卫"},
      {number: 6, name: "Otabek Shukurov", name_zh: "舒库罗夫", position: "CM", position_zh: "中前卫"},
      {number: 7, name: "Jaloliddin Masharipov", name_zh: "马沙里波夫", position: "LW", position_zh: "左边锋"},
      {number: 8, name: "Odiljon Hamrobekov", name_zh: "哈姆罗别科夫", position: "CDM", position_zh: "后腰"},
      {number: 9, name: "Eldor Shomurodov", name_zh: "肖穆罗多夫", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Abbosbek Fayzullaev", name_zh: "法伊祖拉耶夫", position: "RW", position_zh: "右边锋"},
      {number: 11, name: "Dostonbek Khamdamov", name_zh: "哈姆达莫夫", position: "CAM", position_zh: "前腰"},
      {number: 12, name: "Sukhrob Nurullaev", name_zh: "努鲁拉耶夫", position: "GK", position_zh: "门将"},
      {number: 13, name: "Bobir Abdixolikov", name_zh: "阿卜迪霍利科夫", position: "ST", position_zh: "前锋"},
      {number: 14, name: "Sardor Rashidov", name_zh: "拉希多夫", position: "LW", position_zh: "左边锋"},
      {number: 15, name: "Rustamjon Ashurmatov", name_zh: "阿舒尔马托夫", position: "CB", position_zh: "中后卫"},
      {number: 16, name: "Islom Kenzhaboev", name_zh: "肯扎博耶夫", position: "RB", position_zh: "右后卫"},
      {number: 17, name: "Oston Urunov", name_zh: "乌鲁诺夫", position: "RW", position_zh: "右边锋"},
      {number: 18, name: "Mukhamadali Urinboyev", name_zh: "乌林博耶夫", position: "CM", position_zh: "中前卫"},
      {number: 19, name: "Nurbek Mavlankulov", name_zh: "马夫兰库洛夫", position: "CB", position_zh: "中后卫"},
      {number: 20, name: "Sanjar Qodirov", name_zh: "科迪罗夫", position: "GK", position_zh: "门将"}
    ],
    recent_form: "WWDLWWWDWL", goals_scored_last10: 16, goals_conceded_last10: 8
  },
  {
    code: "PAN", name: "Panama", name_zh: "巴拿马", group: "L", flag_emoji: "🇵🇦",
    elo_rating: 1560, fifa_rank: 63, confederation: "CONCACAF", formation: "4-4-2",
    key_players: [
      {name: "Adalberto Carrasquilla", position: "CM"},
      {name: "Ismael Díaz", position: "ST"},
      {name: "Aníbal Godoy", position: "CDM"},
      {name: "Michael Murillo", position: "RB"},
      {name: "José Luis Rodríguez", position: "LW"}
    ],
    squad: [
      {number: 1, name: "Luis Mejía", name_zh: "梅希亚", position: "GK", position_zh: "门将"},
      {number: 2, name: "Michael Murillo", name_zh: "穆里略", position: "RB", position_zh: "右后卫"},
      {number: 3, name: "Eric Davis", name_zh: "戴维斯", position: "LB", position_zh: "左后卫"},
      {number: 4, name: "Andrés Andrade", name_zh: "安德拉德", position: "CB", position_zh: "中后卫"},
      {number: 5, name: "Fidel Escobar", name_zh: "埃斯科瓦尔", position: "CB", position_zh: "中后卫"},
      {number: 6, name: "Aníbal Godoy", name_zh: "戈多伊", position: "CDM", position_zh: "后腰"},
      {number: 7, name: "Adalberto Carrasquilla", name_zh: "卡拉斯基亚", position: "CM", position_zh: "中前卫"},
      {number: 8, name: "José Luis Rodríguez", name_zh: "罗德里格斯", position: "LW", position_zh: "左边锋"},
      {number: 9, name: "Ismael Díaz", name_zh: "伊斯梅尔·迪亚斯", position: "ST", position_zh: "前锋"},
      {number: 10, name: "Yoel Bárcenas", name_zh: "巴塞纳斯", position: "CAM", position_zh: "前腰"},
      {number: 11, name: "Cecilio Waterman", name_zh: "沃特曼", position: "RW", position_zh: "右边锋"},
      {number: 12, name: "Orlando Mosquera", name_zh: "莫斯克拉", position: "GK", position_zh: "门将"},
      {number: 13, name: "Harold Cummings", name_zh: "卡明斯", position: "CB", position_zh: "中后卫"},
      {number: 14, name: "Armando Cooper", name_zh: "库珀", position: "CM", position_zh: "中前卫"},
      {number: 15, name: "Abdiel Ayarza", name_zh: "阿亚尔萨", position: "ST", position_zh: "前锋"},
      {number: 16, name: "Roderick Miller", name_zh: "米勒", position: "CB", position_zh: "中后卫"},
      {number: 17, name: "Alberto Quintero", name_zh: "金特罗", position: "RW", position_zh: "右边锋"},
      {number: 18, name: "Édgar Bárcenas", name_zh: "埃德加·巴塞纳斯", position: "LW", position_zh: "左边锋"},
      {number: 19, name: "Víctor Griffith", name_zh: "格里菲斯", position: "CB", position_zh: "中后卫"},
      {number: 20, name: "Walter Calderón", name_zh: "卡尔德隆", position: "GK", position_zh: "门将"}
    ],
    recent_form: "LWDWLWLLDW", goals_scored_last10: 10, goals_conceded_last10: 14
  }
];

// Add new teams to map
newTeams.forEach(t => { teamsMap[t.code] = t; });

// Build final team list ordered by group then code
const groupOrder = ['A','B','C','D','E','F','G','H','I','J','K','L'];
const allTeams = Object.values(teamsMap);
allTeams.sort((a, b) => {
  const ga = groupOrder.indexOf(a.group);
  const gb = groupOrder.indexOf(b.group);
  if (ga !== gb) return ga - gb;
  return a.code.localeCompare(b.code);
});

const output = {
  tournament: "2026 FIFA World Cup",
  host: "United States, Canada, Mexico",
  year: 2026,
  teams: allTeams
};

fs.writeFileSync('d:/UI/world/data/teams.json', JSON.stringify(output, null, 2), 'utf8');

// Verify
const verify = JSON.parse(fs.readFileSync('d:/UI/world/data/teams.json', 'utf8'));
console.log('Total teams:', verify.teams.length);
console.log('Teams by group:');
const groups = {};
verify.teams.forEach(t => {
  if (!groups[t.group]) groups[t.group] = [];
  groups[t.group].push(t.code);
});
Object.keys(groups).sort().forEach(g => {
  console.log(`  Group ${g}: ${groups[g].join(', ')} (${groups[g].length})`);
});
