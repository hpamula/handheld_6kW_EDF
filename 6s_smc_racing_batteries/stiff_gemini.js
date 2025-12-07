(async function scrapeSMC_Flexible() {
  console.log("Starting flexible scraper... please wait.");

  // 1. Setup Keywords
  const keywords = [
    "True mAh +/- 5%:",
    "Voltage:",
    "C rate:",
    "Power Factor:",
    "Size:",
    "Weight:",
    "Wire size:",
    "Charge rate:"
  ];

  // 2. Identify container and get links
  const container = document.querySelector("#content > div:nth-child(7)");
  if (!container) {
    console.error("Could not find the product list container (div:nth-child(7)).");
    return;
  }

  const productLinks = Array.from(
    container.querySelectorAll("div > div > div.image > a")
  ).map(a => a.href);

  console.log(`Found ${productLinks.length} products. Fetching data...`);

  const allData = [];
  const parser = new DOMParser();

  // 3. Helper function to find text based on keyword
  const getValByKeyword = (doc, key) => {
    // Select all potential text containers within the description tab
    const candidates = Array.from(
      doc.querySelectorAll("#tab-description p, #tab-description h3, #tab-description li, #tab-description span, #tab-description div")
    );

    // Filter for elements that start with the keyword
    const matches = candidates.filter(el => 
      el.textContent && el.textContent.trim().startsWith(key)
    );

    if (matches.length === 0) return "N/A";

    // If matches are nested (e.g. <p><span>Voltage:</span>...</p>), pick the shortest one 
    // to get the most specific element and avoid grabbing a huge parent container.
    const bestMatch = matches.reduce((a, b) => 
      a.textContent.length < b.textContent.length ? a : b
    );

    // Remove the keyword from the start and trim whitespace
    return bestMatch.textContent.trim().substring(key.length).trim();
  };

  // 4. Helper for Name
  const getName = (doc) => {
    // Try user's selector first, fall back to standard H1 if that fails
    const userSel = doc.querySelector("#tab-description > h4 > span");
    if (userSel) return userSel.textContent.trim();
    
    const h1 = doc.querySelector("#content h1");
    return h1 ? h1.textContent.trim() : "N/A";
  };

  // 5. Main Loop
  for (let i = 0; i < productLinks.length; i++) {
    const url = productLinks[i];
    console.log(`Processing ${i + 1}/${productLinks.length}: ${url}`);

    try {
      const response = await fetch(url);
      const htmlText = await response.text();
      const doc = parser.parseFromString(htmlText, "text/html");

      const productData = [];

      // 1. Get Name
      productData.push(getName(doc));

      // 2. Get properties based on keywords
      keywords.forEach(key => {
        productData.push(getValByKeyword(doc, key));
      });

      allData.push(productData);

    } catch (err) {
      console.error(`Failed to fetch ${url}`, err);
      // Push error row
      const errRow = new Array(keywords.length + 1).fill("Error");
      allData.push(errRow);
    }

    // Short delay
    await new Promise(r => setTimeout(r, 100));
  }

  // 6. Output
  console.log("Finished!");
  console.log("---------------------------------------------------");
  console.log(JSON.stringify(allData, null, 2));
  console.log("---------------------------------------------------");

  return allData;
})();