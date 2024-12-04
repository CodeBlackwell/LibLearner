const puppeteer = require('puppeteer');

async function extractGalleryStructure(page) {
    return await page.evaluate(() => {
        const container = document.querySelector('#portfolio_landing > div');
        if (!container) {
            return null;
        }

        const structure = {};
        let currentCategory = null;

        container.childNodes.forEach(node => {
            if (node.tagName === 'P' && node.classList.contains('grpdependant')) {
                currentCategory = node.textContent.trim();
                structure[currentCategory] = [];
            }
            else if (node.tagName === 'DIV' && node.classList.contains('row') && currentCategory) {
                const items = node.querySelectorAll('.portfolio-item');
                items.forEach(item => {
                    const link = item.querySelector('a.portfolio-link');
                    const caption = item.querySelector('.captionPortfolio');
                    
                    if (link && caption) {
                        const itemData = {
                            title: caption.textContent.trim(),
                            url: link.href,
                            type: currentCategory.toLowerCase()
                        };
                        structure[currentCategory].push(itemData);
                    }
                });
            }
        });

        return structure;
    });
}

async function verifyPortfolioPages(browser, structure) {
    const verifiedStructure = JSON.parse(JSON.stringify(structure)); // Deep clone
    
    for (const category of Object.keys(verifiedStructure)) {
        console.log(`\nVerifying category: ${category}`);
        
        for (const item of verifiedStructure[category]) {
            const page = await browser.newPage();
            try {
                await page.goto(item.url, { waitUntil: 'domcontentloaded' });
                
                const hasPortfolio = await page.evaluate(() => {
                    const portfolioElement = document.querySelector('#portfolio');
                    return !!portfolioElement;
                });
                
                item.hasPortfolioElement = hasPortfolio;
                console.log(`  ${item.title}: ${hasPortfolio ? '✓' : '✗'}`);
                
            } catch (error) {
                console.error(`  Error checking ${item.title}: ${error.message}`);
                item.hasPortfolioElement = false;
                item.error = error.message;
            } finally {
                await page.close();
            }
        }
    }
    
    return verifiedStructure;
}

async function main() {
    const browser = await puppeteer.launch({ 
        headless: "new",
        defaultViewport: { width: 1920, height: 1080 }
    });

    try {
        const page = await browser.newPage();
        await page.goto('https://d3-graph-gallery.com/index.html', {
            waitUntil: 'domcontentloaded'
        });
        
        const structure = await extractGalleryStructure(page);
        await page.close();
        
        if (structure) {
            console.log('Initial structure extracted. Verifying portfolio pages...\n');
            const verifiedStructure = await verifyPortfolioPages(browser, structure);
            
            // Output final results
            console.log('\nFinal Results:');
            console.log(JSON.stringify(verifiedStructure, null, 2));
            
            // Summary of verification
            console.log('\nVerification Summary:');
            let totalPages = 0;
            let pagesWithPortfolio = 0;
            
            Object.values(verifiedStructure).forEach(category => {
                category.forEach(item => {
                    totalPages++;
                    if (item.hasPortfolioElement) pagesWithPortfolio++;
                });
            });
            
            console.log(`Total pages checked: ${totalPages}`);
            console.log(`Pages with #portfolio: ${pagesWithPortfolio}`);
            console.log(`Success rate: ${((pagesWithPortfolio/totalPages) * 100).toFixed(1)}%`);
        }
    } finally {
        await browser.close();
    }
}

main().catch(console.error);
