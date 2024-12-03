#!/usr/bin/env node
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import cliProgress from 'cli-progress';
import chalk from 'chalk';
import os from 'os';
import * as tar from 'tar';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const CONFIG = {
  requestDelay: 1000,
  baseUrl: 'https://observablehq.com',
  verbose: true,
  systemDownloads: path.join(os.homedir(), 'Downloads')
};

// Create resources directory if it doesn't exist
const resourcesDir = path.join(__dirname, '..', 'resources');
if (!fs.existsSync(resourcesDir)) {
  fs.mkdirSync(resourcesDir, { recursive: true });
}

const notebookSlugs = [
    '@d3/animated-treemap',
    '@d3/temporal-force-directed-graph',
    '@d3/connected-scatterplot/2',
    '@mbostock/the-wealth-health-of-nations',
    '@d3/scatterplot-tour',
    '@d3/bar-chart-race',
    '@d3/stacked-to-grouped-bars',
    '@d3/streamgraph-transitions',
    '@d3/smooth-zooming',
    '@d3/zoom-to-bounding-box',
    '@d3/orthographic-to-equirectangular',
    '@d3/world-tour',
    '@d3/walmarts-growth',
    '@d3/hierarchical-bar-chart',
    '@d3/zoomable-treemap',
    '@d3/zoomable-circle-packing',
    '@d3/collapsible-tree',
    '@d3/zoomable-icicle',
    '@d3/zoomable-sunburst',
    '@d3/bar-chart-transitions/2',
    '@d3/icelandic-population-by-age-1841-2019',
    '@d3/pie-chart-update',
    '@d3/arc-tween',
    '@d3/versor-dragging',
    '@d3/index-chart/2',
    '@kerryrodden/sequences-sunburst',
    '@d3/brushable-scatterplot',
    '@d3/brushable-scatterplot-matrix',
    '@d3/pannable-chart',
    '@d3/zoomable-area-chart',
    '@d3/zoomable-bar-chart',
    '@d3/seamless-zoomable-map-tiles',
    '@d3/moving-average',
    '@d3/bollinger-bands/2',
    "@d3/box-plot/2",
    "@d3/histogram/2",
    "@d3/kernel-density-estimation",
    "@d3/density-contours",
    "@d3/volcano-contours/2",
    "@d3/contours",
    "@d3/hexbin",
    "@d3/hexbin-area",
    "@d3/hexbin-map",
    "@d3/q-q-plot",
    "@d3/normal-quantile-plot",
    "@d3/parallel-sets",
    "@d3/treemap/2",
    "@d3/cascaded-treemap",
    "@d3/nested-treemap",
    "@d3/pack/2",
    "@d3/indented-tree",
    "@d3/tree/2",
    "@d3/radial-tree/2",
    "@d3/cluster/2",
    "@d3/radial-cluster/2",
    "@d3/sunburst/2",
    "@d3/icicle/2",
    "@nitaku/tangled-tree-visualization-ii",
    "@d3/tree-of-life",
    "@d3/force-directed-tree",
    "@d3/force-directed-graph/2",
    "@d3/disjoint-force-directed-graph/2",
    "@d3/mobile-patent-suits",
    "@d3/arc-diagram",
    "@d3/sankey/2",
    "@d3/hierarchical-edge-bundling",
    "@d3/hierarchical-edge-bundling/2",
    "@d3/chord-diagram",
    "@d3/chord-diagram/2",
    "@d3/directed-chord-diagram/2",
    "@d3/chord-dependency-diagram/2",
    "@d3/bar-chart/2",
    "@d3/horizontal-bar-chart/2",
    "@d3/diverging-bar-chart/2",
    "@d3/stacked-bar-chart/2",
    "@d3/stacked-horizontal-bar-chart/2",
    "@d3/stacked-normalized-horizontal-bar/2",
    "@d3/grouped-bar-chart/2",
    "@d3/diverging-stacked-bar-chart/2",
    "@d3/marimekko-chart",
    "@tezzutezzu/world-history-timeline",
    "@d3/calendar/2",
    "@d3/the-impact-of-vaccines",
    "@mbostock/electric-usage-2019",
    "@d3/revenue-by-music-format-1973-2018",
    "@d3/line-chart/2",
    "@d3/line-chart-missing-data/2",
    "@d3/multi-line-chart/2",
    "@d3/change-line-chart/2",
    "@d3/slope-chart/3",
    "@d3/cancer-survival-rates/2",
    "@d3/mareys-trains",
    "@d3/candlestick-chart/2",
    "@d3/variable-color-line",
    "@d3/gradient-encoding",
    "@d3/threshold-encoding",
    "@d3/parallel-coordinates",
    "@d3/inequality-in-american-cities",
    "@d3/new-zealand-tourists-1921-2018",
    "@d3/sea-ice-extent-1978-2017",
    "@d3/area-chart/2",
    "@d3/area-chart-missing-data/2",
    "@d3/stacked-area-chart/2",
    "@d3/normalized-stacked-area-chart/2",
    "@d3/u-s-population-by-state-1790-1990",
    "@d3/streamgraph/2",
    "@d3/difference-chart/2",
    "@d3/band-chart/2",
    "@d3/ridgeline-plot",
    "@d3/horizon-chart/2",
    "@d3/realtime-horizon-chart",
    "@d3/scatterplot/2",
    "@d3/scatterplot-with-shapes",
    "@d3/splom/2",
    "@d3/dot-plot/2",
    "@d3/global-temperature-trends",
    "@d3/bubble-map/2",
    "@d3/spike-map/2",
    "@d3/bubble-chart/2",
    "@d3/beeswarm/2",
    "@d3/beeswarm-mirrored/2",
    "@d3/hertzsprung-russell-diagram",
    "@d3/pie-chart/2",
    "@d3/donut-chart/2",
    "@d3/radial-area-chart/2",
    "@d3/radial-stacked-bar-chart/2",
    "@d3/radial-stacked-bar-chart/3",
    "@d3/inline-labels/2",
    "@harrystevens/directly-labelling-lines",
    "@d3/line-with-tooltip/2",
    "@d3/voronoi-labels",
    "@fil/occlusion",
    "@d3/graticule-labels-stereographic",
    "@d3/styled-axes",
    "@d3/color-legend",
    "@d3/choropleth/2",
    "@d3/bivariate-choropleth",
    "@d3/us-state-choropleth/2",
    "@d3/world-choropleth/2",
    "@d3/world-map",
    "@d3/projection-transitions",
    "@d3/projection-comparison",
    "@d3/antimeridian-cutting",
    "@d3/tissots-indicatrix",
    "@d3/web-mercator-tiles",
    "@d3/raster-tiles",
    "@d3/vector-tiles",
    "@d3/clipped-map-tiles",
    "@d3/raster-vector",
    "@d3/vector-field",
    "@d3/geotiff-contours-ii",
    "@d3/us-airports-voronoi",
    "@d3/world-airports-voronoi",
    "@d3/solar-terminator",
    "@d3/solar-path",
    "@d3/star-map",
    "@d3/non-contiguous-cartogram",
    "@d3/d3-packenclose",
    "@veltman/centerline-labeling",
    "@mbostock/methods-of-comparison-compared",
    "@mbostock/predator-and-prey",
    "@mbostock/polar-clock",
    "@mbostock/stern-brocot-tree",
    "@mbostock/voronoi-stippling",
    "@veltman/watercolor",
    "@d3/psr-b1919-21",
    "@d3/epicyclic-gearing",
    "@mbostock/owls-to-the-max",
    "@mbostock/tadpoles",
    "@d3/word-cloud",
    "@d3/spilhaus-shoreline-map",
    '@mbostock/phases-of-the-moon',
    '@d3/color-schemes'
];

// Function to wait for download in system Downloads folder
const waitForDownload = (timeout = 10000) => {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const initialFiles = new Set(fs.readdirSync(CONFIG.systemDownloads));
      
      const checkDownload = () => {
        const currentFiles = new Set(fs.readdirSync(CONFIG.systemDownloads));
        const newFiles = [...currentFiles].filter(file => !initialFiles.has(file));
        
        // Look for new .tgz files
        const newDownloads = newFiles.filter(file => file.endsWith('.tgz'));
        
        if (newDownloads.length > 0) {
          resolve(newDownloads[0]); // Return the first new .tgz file
        } else if (Date.now() - startTime > timeout) {
          reject(new Error('Download timeout'));
        } else {
          setTimeout(checkDownload, 100);
        }
      };
      
      checkDownload();
    });
  };
  
  // Function to move downloaded file to target directory
  const moveDownloadedFile = (sourcePath, targetDir) => {
    const fileName = path.basename(sourcePath);
    const targetPath = path.join(targetDir, fileName);
    
    fs.renameSync(sourcePath, targetPath);
    return targetPath;
  };

  // Function to extract .tgz file
  const extractTgz = async (tgzPath, extractDir) => {
    const notebookName = path.basename(tgzPath, '.tgz');
    const targetDir = path.join(extractDir, notebookName);
    
    // Create target directory
    fs.mkdirSync(targetDir, { recursive: true });
    
    try {
      console.log(chalk.yellow(`📦 Extracting ${notebookName}...`));
      
      // Extract the .tgz file
      await tar.x({
        file: tgzPath,
        cwd: targetDir,
        strip: 1
      });
      
      // Clean up the .tgz file
      fs.unlinkSync(tgzPath);
      console.log(chalk.green(`🗑️  Cleaned up ${path.basename(tgzPath)}`));
      
      return targetDir;
    } catch (error) {
      throw error;
    }
  };

  (async () => {
    console.log(chalk.blue('🚀 Starting ObservableHQ notebook downloader...'));
    
    const multibar = new cliProgress.MultiBar({
      clearOnComplete: false,
      hideCursor: true,
      format: '{bar} {percentage}% | {value}/{total} | {status}'
    }, cliProgress.Presets.shades_classic);
  
    const mainBar = multibar.create(notebookSlugs.length, 0, { status: 'Notebooks processed' });
    
    const browser = await puppeteer.launch({
      headless: false,
      defaultViewport: null
    });
    
    // Create download directory
    const downloadPath = path.join(resourcesDir, 'notebooks');
    fs.mkdirSync(downloadPath, { recursive: true });
    
    console.log(chalk.yellow(`📁 Target directory: ${downloadPath}`));
    console.log(chalk.yellow(`🔍 Monitoring downloads in: ${CONFIG.systemDownloads}`));
  
    for (let [index, slug] of notebookSlugs.entries()) {
      try {
        if (index > 0) {
          await new Promise(resolve => setTimeout(resolve, CONFIG.requestDelay));
        }
        
        const url = `${CONFIG.baseUrl}/${slug}`;
        if (CONFIG.verbose) console.log(chalk.blue(`\n📥 Processing notebook: ${slug}`));
        
        const page = await browser.newPage();
        await page.goto(url, { waitUntil: 'networkidle2' });
        const notebookTitle = await page.title();
        
        // Click the "..." menu button
        await page.waitForSelector('button[aria-haspopup="true"][class*="action-button"]');
        await page.click('button[aria-haspopup="true"][class*="action-button"]');
        
        // Wait for and click the Export option
        await page.waitForSelector('[role="menuitem"][data-valuetext="Export"]');
        await page.click('[role="menuitem"][data-valuetext="Export"]');
        
        // Wait a moment for submenu
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Now look for and click the download option in the submenu
        await page.evaluate(() => {
          const menuItems = Array.from(document.querySelectorAll('[role="menuitem"]'));
          const downloadItem = menuItems.find(item => 
            item.textContent.includes('Download zip') || 
            item.textContent.includes('Download')
          );
          if (downloadItem) downloadItem.click();
        });
        
        console.log(chalk.yellow('⏳ Waiting for download to complete...'));
        const downloadedFile = await waitForDownload();
        
        // Move the file to our target directory
        const finalPath = moveDownloadedFile(path.join(CONFIG.systemDownloads, downloadedFile), downloadPath);
        
        console.log(chalk.green(`✅ Successfully downloaded: ${notebookTitle}`));
        console.log(chalk.blue(`📦 Saved to: ${finalPath}`));

        // Extract and cleanup
        const extractedDir = await extractTgz(finalPath, downloadPath);
        console.log(chalk.blue(`📂 Files extracted to: ${extractedDir}`));
        
        mainBar.increment();

        // Close the tab after download completes
        await page.close();
      } catch (error) {
        console.error(chalk.red(`❌ Failed to download ${slug}:`), error);
        mainBar.increment({ status: 'Error occurred' });
        // Make sure to close the tab even if there's an error
        try {
          await page.close();
        } catch (e) {
          // Ignore any errors from closing the page
        }
      }
    }
  
    multibar.stop();
    console.log(chalk.green('\n🎉 Downloads completed!'));
    await browser.close();
  })();