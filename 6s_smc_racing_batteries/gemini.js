(async function scrapeSMC_Complete() {
  console.log("Starting complete scraper (Header + Tabs)... please wait.");

  // 1. Define Fields
  // Added your requested fields. 
  // Note: I renamed the name "$" to "Price" for better readability in the output.
  const fieldDefinitions = [
    { 
      name: "Price", 
      aliases: ["$"] 
    },
    { 
      name: "Availability", 
      aliases: ["Availability:"] 
    },
    { 
      name: "Product_Code", 
      aliases: ["Product Code:"] 
    },
    { 
      name: "mAh", 
      aliases: ["True mAh +/- 5%:", "mAh +/- 5%:"] 
    },
    { 
      name: "Voltage", 
      aliases: ["Voltage:"] 
    },
    { 
      name: "C_Rate", 
      aliases: ["C rate:", "Factory C rate:"] 
    },
    { 
      name: "Power_Factor", 
      aliases: ["Power Factor:"] 
    },
    { 
      name: "Size", 
      aliases: ["Size:"] 
    },
    { 
      name: "Weight", 
      aliases: ["Weight:", "Weight +/- 10gr:", "Weight +/- 5gr:"] 
    },
    { 
      name: "Wire_Size", 
      aliases: ["Wire size:"] 
    },
    { 
      name: "Charge_Rate", 
      aliases: ["Charge rate:"] 
    }
  ];

  // 2. Identify main list container
  const container = document.querySelector("#content > div:nth-child(7)");
  if (!container) {
    console.error("Could not find the product list container.");
    return;
  }

  const productLinks = Array.from(
    container.querySelectorAll("div > div > div.image > a")
  ).map(a => a.href);

  console.log(`Found ${productLinks.length} products. Fetching data...`);

  const allData = [];
  const parser = new DOMParser();

  // 3. Helper: Search for keyword in the WHOLE content area
  const findValueByKeyword = (doc, keyword) => {
    // CHANGE: Previously used "#tab-description". 
    // Now using "#content" to catch the Header info (Price/Code) AND the Description tabs.
    const contentArea = doc.querySelector("#content"); 
    if (!contentArea) return null;

    // Get all elements inside #content
    const allElements = Array.from(contentArea.querySelectorAll("*"));

    // Find elements starting with the keyword (Case Insensitive)
    const matches = allElements.filter(el => 
      el.textContent && el.textContent.trim().toUpperCase().startsWith(keyword.toUpperCase())
    );

    if (matches.length === 0) return null;

    // Sort by length (shortest first) to get the specific element (e.g., <h2>$100</h2>), 
    // ignoring the parent containers (e.g., <div>...<h2>$100</h2>...</div>)
    matches.sort((a, b) => a.textContent.length - b.textContent.length);
    
    // Pick the shortest match
    const bestElement = matches[0];
    const fullText = bestElement.textContent.trim();

    // Remove the keyword itself to return just the value
    // e.g. "$162.95" (keyword "$") -> "162.95"
    return fullText.substring(keyword.length).trim();
  };

  // 4. Helper: Loop through aliases
  const getFieldData = (doc, fieldDef) => {
    for (const alias of fieldDef.aliases) {
      const result = findValueByKeyword(doc, alias);
      if (result !== null) {
        return result; 
      }
    }
    return "N/A";
  };

  // 5. Helper: Get Name
  const getName = (doc) => {
    const h1 = doc.querySelector("h1");
    return h1 ? h1.textContent.trim() : "N/A";
  };

  // 6. Main Loop
  for (let i = 0; i < productLinks.length; i++) {
    const url = productLinks[i];
    console.log(`Processing ${i + 1}/${productLinks.length}: ${url}`);

    try {
      const response = await fetch(url);
      const htmlText = await response.text();
      const doc = parser.parseFromString(htmlText, "text/html");

      const productData = [];

      productData.push(getName(doc));

      fieldDefinitions.forEach(def => {
        productData.push(getFieldData(doc, def));
      });

      allData.push(productData);

    } catch (err) {
      console.error(`Failed to fetch ${url}`, err);
      const errRow = new Array(fieldDefinitions.length + 1).fill("Error");
      allData.push(errRow);
    }
    
    await new Promise(r => setTimeout(r, 100)); // Be polite to the server
  }

  // 7. Output
  console.log("Finished!");
  console.log("---------------------------------------------------");
  console.log(JSON.stringify(allData, null, 2));
  console.log("---------------------------------------------------");
  
  return allData;
})();