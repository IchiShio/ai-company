// NewsUp: VOA-style news articles with comprehension questions
const newsArticles = [
  {
    id: "n001",
    title: "Scientists Discover New Deep-Sea Fish Near Japan",
    level: "B1",
    category: "Science",
    text: `Scientists have discovered a new species of fish in the deep ocean near Japan. The fish, which lives more than 3,000 meters below the surface, has no eyes and produces its own light. Researchers from Tokyo University found the creature during a six-month expedition. They used special underwater robots to capture video footage of the animal. "This discovery shows that the deep ocean is still full of mysteries," said Dr. Yuki Tanaka, who led the research team. The fish feeds on small shrimp and bacteria that live near underwater volcanoes. Scientists plan to study the creature's DNA to learn more about its evolution. The findings were published in the journal Nature this week.`,
    questions: [
      {
        question: "Where was the new fish species discovered?",
        options: ["In the Atlantic Ocean", "Near Japan in the deep ocean", "In a freshwater lake", "Near Australia"],
        answer: "Near Japan in the deep ocean",
        explanation: "The article says the fish was found 'in the deep ocean near Japan.'"
      },
      {
        question: "How deep does this fish live?",
        options: ["More than 300 meters", "More than 1,000 meters", "More than 3,000 meters", "More than 5,000 meters"],
        answer: "More than 3,000 meters",
        explanation: "The text states the fish 'lives more than 3,000 meters below the surface.'"
      },
      {
        question: "What did researchers use to record the fish?",
        options: ["Scuba divers", "Submarines", "Underwater robots", "Fishing nets"],
        answer: "Underwater robots",
        explanation: "The article states they 'used special underwater robots to capture video footage.'"
      }
    ],
    vocabulary: [
      { word: "species", meaning: "a group of living things of the same type" },
      { word: "expedition", meaning: "a journey made for a specific purpose" },
      { word: "evolution", meaning: "the gradual development of living things over time" }
    ]
  },
  {
    id: "n002",
    title: "Electric Cars Outsell Gasoline Cars in Norway",
    level: "B1",
    category: "Environment",
    text: `For the first time in history, electric cars have outsold gasoline-powered cars in Norway. Last year, electric vehicles made up 54 percent of all new car sales in the country. The Norwegian government has supported electric cars for many years by removing taxes and offering free parking. Norway also has a large network of charging stations across the country. "We are proud to be leading the world in this area," said Transport Minister Lars Hansen. Other European countries are watching Norway's success closely. Germany and France have also started offering discounts to people who buy electric cars. Experts believe that electric vehicles could make up half of all new car sales worldwide by 2035.`,
    questions: [
      {
        question: "What percentage of new cars sold in Norway last year were electric?",
        options: ["34 percent", "44 percent", "54 percent", "64 percent"],
        answer: "54 percent",
        explanation: "The article clearly states 'electric vehicles made up 54 percent of all new car sales.'"
      },
      {
        question: "How has the Norwegian government supported electric cars?",
        options: ["By building more roads", "By removing taxes and offering free parking", "By banning gasoline cars", "By giving free cars to citizens"],
        answer: "By removing taxes and offering free parking",
        explanation: "The text says Norway has supported electric cars 'by removing taxes and offering free parking.'"
      },
      {
        question: "By what year do experts believe electric vehicles could make up half of new car sales worldwide?",
        options: ["2025", "2030", "2035", "2040"],
        answer: "2035",
        explanation: "The article ends with 'electric vehicles could make up half of all new car sales worldwide by 2035.'"
      }
    ],
    vocabulary: [
      { word: "outsell", meaning: "to sell more than something else" },
      { word: "network", meaning: "a system of connected things" },
      { word: "discount", meaning: "a reduction in the usual price" }
    ]
  },
  {
    id: "n003",
    title: "India Launches First Crewed Moon Mission",
    level: "B2",
    category: "Space",
    text: `India has announced plans to send its first astronauts to the Moon by 2030. The Indian Space Research Organisation, known as ISRO, revealed the ambitious project at a press conference in New Delhi. The mission, called Gaganyaan Lunar, will require three astronauts to travel for approximately four days before reaching the lunar surface. India already successfully landed an uncrewed spacecraft near the Moon's south pole in 2023. "Building on that success, we are ready for the next great step," said ISRO Director Dr. Priya Menon. The mission will cost approximately $1.5 billion. India will partner with Japan and Australia on certain technical aspects of the project. The announcement has drawn significant international attention, as only the United States, the Soviet Union, and China have previously sent humans to the Moon.`,
    questions: [
      {
        question: "When does India plan to send astronauts to the Moon?",
        options: ["By 2025", "By 2028", "By 2030", "By 2035"],
        answer: "By 2030",
        explanation: "The article states India plans to 'send its first astronauts to the Moon by 2030.'"
      },
      {
        question: "How long will the journey to the lunar surface take?",
        options: ["One day", "Two days", "Three days", "Approximately four days"],
        answer: "Approximately four days",
        explanation: "The text says astronauts will travel 'for approximately four days before reaching the lunar surface.'"
      },
      {
        question: "Which countries have previously sent humans to the Moon?",
        options: ["USA, Russia, China", "USA, Soviet Union, China", "USA, Japan, China", "USA, Soviet Union, India"],
        answer: "USA, Soviet Union, China",
        explanation: "The article mentions 'the United States, the Soviet Union, and China have previously sent humans to the Moon.'"
      }
    ],
    vocabulary: [
      { word: "crewed", meaning: "carrying human crew members" },
      { word: "ambitious", meaning: "requiring a lot of effort to achieve" },
      { word: "lunar", meaning: "relating to the Moon" }
    ]
  },
  {
    id: "n004",
    title: "Global Coffee Shortage Expected This Year",
    level: "B1",
    category: "Economy",
    text: `Coffee prices are rising worldwide as experts warn of a global shortage. Unusual weather patterns in Brazil and Vietnam — the world's two largest coffee producers — have damaged crops this year. Heavy rains followed by long dry periods destroyed about 20 percent of expected harvests. Coffee shop owners in major cities are already raising their prices. A cup of coffee in New York now costs an average of $6.50, up from $5.00 last year. "This situation will likely last at least 18 months," said food economist Maria Santos. Consumers in Japan and South Korea, which import large quantities of coffee, are particularly concerned. Some supermarkets have already started limiting how much coffee one customer can buy. Experts recommend that coffee lovers consider switching to tea or locally grown alternatives.`,
    questions: [
      {
        question: "Which two countries are the world's largest coffee producers?",
        options: ["Colombia and Ethiopia", "Brazil and Vietnam", "Brazil and Colombia", "Vietnam and Indonesia"],
        answer: "Brazil and Vietnam",
        explanation: "The article identifies 'Brazil and Vietnam' as 'the world's two largest coffee producers.'"
      },
      {
        question: "How much does a cup of coffee now cost on average in New York?",
        options: ["$4.50", "$5.00", "$5.50", "$6.50"],
        answer: "$6.50",
        explanation: "The text states 'A cup of coffee in New York now costs an average of $6.50.'"
      },
      {
        question: "What percentage of expected harvests was destroyed?",
        options: ["About 10 percent", "About 15 percent", "About 20 percent", "About 25 percent"],
        answer: "About 20 percent",
        explanation: "The article says unusual weather 'destroyed about 20 percent of expected harvests.'"
      }
    ],
    vocabulary: [
      { word: "shortage", meaning: "a situation where there is not enough of something" },
      { word: "harvest", meaning: "the process of collecting crops" },
      { word: "economist", meaning: "an expert who studies money and trade" }
    ]
  },
  {
    id: "n005",
    title: "AI Tool Helps Doctors Detect Cancer Earlier",
    level: "B2",
    category: "Health",
    text: `A new artificial intelligence system developed by researchers at Oxford University can detect certain types of cancer up to two years earlier than current methods. The AI tool analyzes blood test results and looks for tiny chemical signals that appear before tumors become visible on scans. In a trial involving 10,000 patients, the system correctly identified cancer in 94 percent of cases. "Early detection is the key to saving lives," said Professor James Walker, who led the study. The technology is currently being tested in hospitals in the United Kingdom and Canada. However, some doctors warn that AI tools should assist, not replace, human judgment. The researchers hope the system will receive regulatory approval within three years and could eventually be used in routine health checkups worldwide.`,
    questions: [
      {
        question: "How much earlier can the AI tool detect cancer compared to current methods?",
        options: ["Up to six months", "Up to one year", "Up to two years", "Up to three years"],
        answer: "Up to two years",
        explanation: "The article says the AI can detect cancer 'up to two years earlier than current methods.'"
      },
      {
        question: "How many patients were involved in the trial?",
        options: ["1,000", "5,000", "10,000", "50,000"],
        answer: "10,000",
        explanation: "The text mentions 'a trial involving 10,000 patients.'"
      },
      {
        question: "What do some doctors warn about AI tools?",
        options: ["They are too expensive to use", "They should assist, not replace, human judgment", "They are not accurate enough", "They require too much training data"],
        answer: "They should assist, not replace, human judgment",
        explanation: "The article states 'some doctors warn that AI tools should assist, not replace, human judgment.'"
      }
    ],
    vocabulary: [
      { word: "detect", meaning: "to discover or identify something" },
      { word: "tumor", meaning: "an abnormal growth in the body" },
      { word: "regulatory approval", meaning: "official permission from a government authority" }
    ]
  },
  {
    id: "n006",
    title: "Remote Work Becomes Permanent at Many Companies",
    level: "B1",
    category: "Business",
    text: `Many large companies worldwide have decided to make remote work a permanent option for their employees. A recent survey of 500 companies found that 65 percent now offer full-time remote work, while another 30 percent offer hybrid arrangements. "The pandemic showed us that people can be just as productive working from home," said business consultant Angela Chen. Workers report higher job satisfaction and less stress when they work remotely. However, some managers worry about team communication and company culture. Cities like San Francisco and New York have seen office vacancy rates rise to 25 percent as fewer workers commute daily. Real estate experts predict that many office buildings will be converted into apartments or hotels in the coming years.`,
    questions: [
      {
        question: "What percentage of companies surveyed now offer full-time remote work?",
        options: ["35 percent", "50 percent", "65 percent", "75 percent"],
        answer: "65 percent",
        explanation: "The article states '65 percent now offer full-time remote work.'"
      },
      {
        question: "What concerns do some managers have about remote work?",
        options: ["Employee salaries are too high", "Workers are not productive enough", "Team communication and company culture", "Internet connections are unreliable"],
        answer: "Team communication and company culture",
        explanation: "The text says 'some managers worry about team communication and company culture.'"
      },
      {
        question: "What do real estate experts predict will happen to many office buildings?",
        options: ["They will be demolished", "They will be expanded", "They will be converted into apartments or hotels", "They will be rented to smaller companies"],
        answer: "They will be converted into apartments or hotels",
        explanation: "The article predicts 'many office buildings will be converted into apartments or hotels.'"
      }
    ],
    vocabulary: [
      { word: "permanent", meaning: "lasting for a long time or forever" },
      { word: "hybrid", meaning: "a mix of two different things" },
      { word: "vacancy", meaning: "an empty space that is available" }
    ]
  },
  {
    id: "n007",
    title: "Ocean Cleanup Project Removes Record Plastic",
    level: "B1",
    category: "Environment",
    text: `An international ocean cleanup project has removed a record amount of plastic waste from the Pacific Ocean this year. The organization, called Ocean Guardian, collected 8,500 tons of plastic during a six-month operation. Special ships equipped with large nets scooped up floating plastic, which was then transported to recycling facilities on land. "Every piece of plastic we remove is one less threat to marine life," said project director Sven Olsson. Scientists estimate that approximately 8 million tons of plastic enter the world's oceans every year. Fish, sea turtles, and seabirds often mistake plastic for food, which can be fatal. The organization plans to expand its operations to the Atlantic and Indian Oceans next year, with funding from several major technology companies.`,
    questions: [
      {
        question: "How much plastic did Ocean Guardian collect this year?",
        options: ["850 tons", "4,500 tons", "8,500 tons", "8 million tons"],
        answer: "8,500 tons",
        explanation: "The article states Ocean Guardian 'collected 8,500 tons of plastic.'"
      },
      {
        question: "How does plastic harm marine animals?",
        options: ["It changes the water temperature", "Animals often mistake it for food", "It blocks sunlight from reaching underwater", "It causes oil spills"],
        answer: "Animals often mistake it for food",
        explanation: "The text says 'Fish, sea turtles, and seabirds often mistake plastic for food.'"
      },
      {
        question: "Where does Ocean Guardian plan to expand operations next year?",
        options: ["The Arctic Ocean", "The Mediterranean Sea", "The Atlantic and Indian Oceans", "The Caribbean Sea"],
        answer: "The Atlantic and Indian Oceans",
        explanation: "The article states the plan 'to expand its operations to the Atlantic and Indian Oceans next year.'"
      }
    ],
    vocabulary: [
      { word: "marine", meaning: "relating to the sea" },
      { word: "fatal", meaning: "causing death" },
      { word: "facility", meaning: "a place built for a specific purpose" }
    ]
  },
  {
    id: "n008",
    title: "New High-Speed Rail Line Connects Tokyo and Osaka in 40 Minutes",
    level: "B1",
    category: "Technology",
    text: `Japan has opened a new maglev train line connecting Tokyo and Osaka in just 40 minutes, cutting travel time by more than half compared to the current Shinkansen service. The magnetic levitation train travels at speeds of up to 500 kilometers per hour, making it the fastest passenger train in the world. The project took 15 years and cost approximately $90 billion to complete. Thousands of passengers boarded the first trains on opening day, with many saying the ride was surprisingly smooth and quiet. "This is the future of transportation," said Prime Minister Kenji Yamamoto at the opening ceremony. Environmental groups have praised the project because the maglev trains use significantly less energy than airplanes for the same distance. Tickets cost slightly more than current Shinkansen fares but are expected to become cheaper as more passengers use the service.`,
    questions: [
      {
        question: "How fast does the new maglev train travel?",
        options: ["Up to 300 km/h", "Up to 400 km/h", "Up to 500 km/h", "Up to 600 km/h"],
        answer: "Up to 500 km/h",
        explanation: "The article states the train 'travels at speeds of up to 500 kilometers per hour.'"
      },
      {
        question: "How long did it take to complete the project?",
        options: ["5 years", "10 years", "15 years", "20 years"],
        answer: "15 years",
        explanation: "The text says 'The project took 15 years and cost approximately $90 billion.'"
      },
      {
        question: "Why have environmental groups praised the maglev trains?",
        options: ["They are cheaper than current trains", "They produce no noise pollution", "They use less energy than airplanes", "They carry more passengers per trip"],
        answer: "They use less energy than airplanes",
        explanation: "The article says environmental groups praised the project because 'the maglev trains use significantly less energy than airplanes.'"
      }
    ],
    vocabulary: [
      { word: "levitation", meaning: "the ability to rise and stay in the air" },
      { word: "fare", meaning: "the price paid to travel on a train or bus" },
      { word: "ceremony", meaning: "a formal event held to celebrate something" }
    ]
  },
  {
    id: "n009",
    title: "Children Spend More Time Outdoors in Nordic Countries",
    level: "B1",
    category: "Education",
    text: `Schools in Finland, Sweden, and Norway are increasing outdoor learning time for children, and research suggests it is having positive effects. Students who spend at least two hours outdoors each school day show better concentration, lower stress levels, and improved social skills compared to those who stay indoors. The approach, known as "friluftsliv" in Norwegian, means "open-air living" and has deep cultural roots in Nordic countries. Teachers say outdoor lessons work well for many subjects, including science, mathematics, and even language learning. "Children learn better when they can touch, see, and experience things directly," said education researcher Dr. Anna Lindqvist. Several schools in the United States, Canada, and Japan have started similar programs after visiting Nordic schools. Critics argue that outdoor learning is more difficult in cities and in countries with extreme weather.`,
    questions: [
      {
        question: "How many hours outdoors each school day is recommended for better results?",
        options: ["At least 30 minutes", "At least one hour", "At least two hours", "At least three hours"],
        answer: "At least two hours",
        explanation: "The article says students spend 'at least two hours outdoors each school day.'"
      },
      {
        question: "What does the Norwegian word 'friluftsliv' mean?",
        options: ["Nature education", "Open-air living", "Forest school", "Active learning"],
        answer: "Open-air living",
        explanation: "The text explains 'friluftsliv' means 'open-air living.'"
      },
      {
        question: "What criticism is mentioned about outdoor learning?",
        options: ["It is too expensive to organize", "Children do not enjoy it", "It is more difficult in cities and in extreme weather", "Teachers need special training"],
        answer: "It is more difficult in cities and in extreme weather",
        explanation: "The article states 'Critics argue that outdoor learning is more difficult in cities and in countries with extreme weather.'"
      }
    ],
    vocabulary: [
      { word: "concentration", meaning: "the ability to focus your attention" },
      { word: "approach", meaning: "a way of doing or thinking about something" },
      { word: "critic", meaning: "a person who expresses disapproval or finds faults" }
    ]
  },
  {
    id: "n010",
    title: "Record Number of People Learn New Language Online",
    level: "B2",
    category: "Education",
    text: `Online language learning platforms reported a record-breaking 300 million active users last year, according to a new industry report. The dramatic growth follows increased demand for multilingual skills in the global job market. Spanish, Mandarin Chinese, and Japanese were the most studied languages, with Japanese seeing the fastest growth at 45 percent compared to the previous year. Language learning apps have improved significantly due to artificial intelligence, offering personalized lesson plans and real-time pronunciation feedback. "The app adapts to each learner's pace and weak points automatically," said Sofia Bianchi, CEO of one leading platform. However, researchers caution that app-based learning works best when combined with conversation practice with native speakers. Employment experts note that bilingual workers earn on average 15 percent more than monolingual colleagues in the same field.`,
    questions: [
      {
        question: "How many active users did online language platforms report last year?",
        options: ["30 million", "100 million", "300 million", "3 billion"],
        answer: "300 million",
        explanation: "The article states platforms reported 'a record-breaking 300 million active users.'"
      },
      {
        question: "Which language saw the fastest growth in learners?",
        options: ["Spanish", "Mandarin Chinese", "Japanese", "French"],
        answer: "Japanese",
        explanation: "The text says 'Japanese seeing the fastest growth at 45 percent compared to the previous year.'"
      },
      {
        question: "According to employment experts, how much more do bilingual workers earn?",
        options: ["5 percent more", "10 percent more", "15 percent more", "20 percent more"],
        answer: "15 percent more",
        explanation: "The article states 'bilingual workers earn on average 15 percent more than monolingual colleagues.'"
      }
    ],
    vocabulary: [
      { word: "multilingual", meaning: "able to speak several languages" },
      { word: "personalized", meaning: "designed for a specific individual" },
      { word: "bilingual", meaning: "able to speak two languages fluently" }
    ]
  }
];
