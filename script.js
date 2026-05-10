// Global storage for 2025 companies data from CSV
window.companiesData2025 = [];
window.companyNewsData = [];

// ===== RATIO DEFINITIONS (unchanged) =====
const RATIO_DEFINITIONS = { /* unchanged */ };

// ===== MAIN CLASS =====
class FinovaScreener {
    constructor() {
        this.charts = {};
        this.latestData = null;
        this.currentCompany = null;
        this.isLoading = false;
        this.charts = {};
        this.initializeEventListeners();
        this.hideDashboard();
        this.updateStatus('Ready to analyze');
    }

    initializeEventListeners() {
        const searchInput = document.getElementById('companySearch');
        const analyzeBtn = document.getElementById('analyzeBtn');

        analyzeBtn.addEventListener('click', () => this.handleSearch());
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSearch();
        });

        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        searchInput.focus();
        this.injectInfoIcons();
    }

    injectInfoIcons() { /* unchanged */ }
    showInfoModal(key, dataRow) { /* unchanged */ }

    async handleSearch() {
        console.log(window.companiesData2025)
        const searchInput = document.getElementById('companySearch');
        const companyName = searchInput.value.trim();
        if (!companyName) return this.showError('Please enter a company name');

        this.setLoading(true);
        this.updateStatus('Analyzing company...');
                try {
    this.setLoading(true);
    this.updateStatus("Analyzing company...");

    const response = await fetch("http://localhost:1025/predict", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-API-KEY": "Finova123456789"
        },
        body: JSON.stringify({
            company: companyName
        })
    });

    if (!response.ok) {
        throw new Error("API request failed");
    }

    const result = await response.json();

    if (result.status === "success") {
        await new Promise(r => setTimeout(r, 800));
        await loadAndPrintCSV();
        console.log(window.companiesData2025)
        await loadNewsCSV();
        await loadManagementAnalysisCSV(); 
        const companyData =await this.findCompanyData(companyName);
        console.log(companyName)     
        console.log(companyData)
        if (companyData) {
            this.currentCompany = companyData;
            await this.displayCompanyData(companyData);
            await this.displayNews(companyData.Ticker);
            await this.shareloadChart(companyData.Ticker);
            this.showDashboard();
            this.updateStatus(`Analysis complete: ${companyData.Ticker}`);
        } else {
            this.showError('Company not found.');
            this.updateStatus('Analysis failed');
        }
    }

} catch (error) {
    console.error(error);
    this.showError("Server error occurred.");
    this.updateStatus("API call failed");
} finally {
    this.setLoading(false);
}
    }

    findCompanyData(companyName) {
        const term = companyName.toLowerCase();
        return window.companiesData2025.find(row =>
            (row.Company_Name || '').toLowerCase().includes(term)
        );
    }

    setLoading(loading) {
        const btn = document.getElementById('analyzeBtn');
        btn.disabled = loading;
    }

    updateStatus(msg) {
        document.getElementById('statusIndicator').textContent = msg;
    }

    showError(msg) {
        const el = document.getElementById('errorMessage');
        el.textContent = msg;
        el.style.display = 'block';
        setTimeout(() => el.style.display = 'none', 4000);
    }

    showDashboard() {
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('dashboard').style.display = 'block';
    }

    hideDashboard() {
        document.getElementById('emptyState').style.display = 'block';
        document.getElementById('dashboard').style.display = 'none';
    }

    switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        document.getElementById(tabName).classList.add('active');
    }

    displayCompanyData(data) {
        this.displayCompanyHeader(data);
        this.displayOverallScore(data);
        this.displayOverview(data);
        this.displayFundamentals(data);
        this.displayGrowth(data);
        this.displayIntrinsicValue(data);
        this.displaySentiment(data);
        this.displayManagement(data);
    }

    displayNews(ticker) {
        if (!window.companyNewsData || !window.companyNewsData.length) {
            this.renderCompanyNews([]);
            return;
        }

        // Map CSV columns to renderer format
        const formattedNews = window.companyNewsData.map(n => ({
            title: n.text || "No headline",
            link: n.link || "#",
            source: n.source || "Unknown",
            date: n.date
                ? new Date(n.date).toLocaleDateString("en-IN")
                : ""
        }));

        this.renderCompanyNews(formattedNews);
    }
    async shareloadChart(ticker) {
        try {
            const response = await fetch(
                `https://manueldominy.pythonanywhere.com//weekly-data?ticker=${ticker}`
            );

            const data = await response.json();

            if (data.error) {
                alert(data.error);
                return;
            }

            this.latestData = data;
            this.sharerenderChart(data);

        } catch (error) {
            console.error("Chart load error:", error);
        }
    }
    sharerenderChart(data) {

        const canvas = document.getElementById("sharechart");
        if (!canvas) return;

        const ctx = canvas.getContext("2d");

        // Destroy old chart if exists
        if (this.charts.shareChart) {
            this.charts.shareChart.destroy();
        }

        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, "rgba(40, 116, 240, 0.25)");
        gradient.addColorStop(1, "rgba(40, 116, 240, 0.02)");

        this.charts.shareChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: data.dates,
                datasets: [{
                    data: data.close,
                    borderColor: "#2874F0",
                    backgroundColor: gradient,
                    borderWidth: 2,
                    tension: 0.35,
                    pointRadius: 0,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: "index",
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        grid: { display: false }
                    },
                    y: {
                        grid: { color: "rgba(0,0,0,0.05)" }
                    }
                }
            }
        });
    }

    renderCompanyNews(newsArray) {
        const container = document.getElementById("newsContainer");
        if (!container) return;

        container.innerHTML = "";

        if (!newsArray || newsArray.length === 0) {
            container.innerHTML = `<div class="metric-row"><span>No news available for this company</span></div>`;
            return;
        }

        // Show source only once at the top
        const sourceHeader = document.createElement("div");
        sourceHeader.className = "metric-row";
        sourceHeader.innerHTML = `<span style="font-weight: 600; color: #4fd1c5;">Source: Google News</span>`;
        container.appendChild(sourceHeader);

        newsArray.forEach(news => {
            const newsDiv = document.createElement("div");
            newsDiv.className = "metric-row";
            
            newsDiv.innerHTML = `
                <div class="news-content">
                    <div class="news-heading">
                        <h5>${news.title}</h5>
                    </div>
                    <div class="news-link">
                        <a href="${news.link}" target="_blank" rel="noopener noreferrer">
                            ${news.link}
                        </a>
                    </div>
                    <div class="news-date-corner">
                        ${news.date}
                    </div>
                </div>
            `;

            container.appendChild(newsDiv);
        });
    }

    // ===== FIXED: Header =====
    displayCompanyHeader(data) {
        document.getElementById('companyName').textContent = data.Ticker || '—';
        document.getElementById('ticker').textContent = data.Ticker || '—';
        document.getElementById('sector').textContent = data.Sector || '—';
        document.getElementById('currentPrice').textContent = data['Current Price'] || '—';
    }

    // ===== FIXED: Overall Score mapping =====
    displayOverallScore(data) {
        const roe = Number(data.ROE) || 0;
        const growth = Number(data['Revenue_YoY_Growth_%']) || 0;
        const sentiment = Number(data.Sentiment) || 0;
        const mgmt = Number(data.FinalManagementScore) || 0;
        const intrinsic = Number(data['Intrinsic Value Per Share']) || 0;

        const overall = Math.round((mgmt));

        document.getElementById('overallScore').textContent = intrinsic;
        document.getElementById('scoreF').textContent = roe;
        document.getElementById('scoreG').textContent = growth;
        document.getElementById('scoreS').textContent = sentiment;
        document.getElementById('scoreM').textContent = mgmt;
    }

    // ===== FIXED: Overview ratios =====
  displayOverview(data) {
        const revenueGrowth = Number(data['Revenue_YoY_Growth_%']) || 0;
        const profitGrowth = Number(data['Profit_YoY_Growth_%']) || 0;
        const sentiment = Number(data.Sentiment) || 0;
        const managementScore = Number(data.FinalManagementScore) || 0;
        const currentPrice = Number(data['Current Price']) || 0;

        const set = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };

        // Company Information
        set('overviewCompany', data.Ticker || '—');
        set('overviewSector', data.Sector || '—');
        set('overviewPrice', currentPrice ? `₹${currentPrice.toFixed(2)}` : '—');
        set('overviewYear', data['Year Analyzed'] || '—');

        // Overall Performance
        set('overviewRevenueGrowth', `${revenueGrowth.toFixed(2)}%`);
        set('overviewProfitGrowth', `${profitGrowth.toFixed(2)}%`);
        set('overviewSentiment', sentiment.toFixed(2));
        set('overviewManagement', `${managementScore.toFixed(2)}`);

        // Summary
        const sentimentText = sentiment > 0.6 ? 'positive' : sentiment < 0.3 ? 'negative' : 'neutral';
        const managementText = managementScore > 70 ? 'strong' : managementScore > 50 ? 'moderate' : 'weak';
        set('overviewSummary', `${data.Ticker} operates in the ${data.Sector} sector with ${sentimentText} market sentiment (${sentiment.toFixed(2)}) and ${managementText} management quality (${managementScore.toFixed(2)}). Revenue growth is ${revenueGrowth.toFixed(2)}% and profit growth is ${profitGrowth.toFixed(2)}%.`);
    }

    // ===== FIXED: Fundamentals computed from CSV =====
    displayFundamentals(data) {
        const revenue = Number(data['Total Revenue']) || 0;
        const netIncome = Number(data['Net Income']) || 0;
        const ebit = Number(data.EBIT) || 0;
        const ocf = Number(data.OCF) || 0;
        const fcf = Number(data.FCF) || 0;
        const taxRate = Number(data['Tax Rate']) || 0;
        const debt = Number(data['Total Debt']) || 0;
        const capex = Number(data.Capex) || 0;
        const da = Number(data['D&A']) || 0;
        const shares = Number(data.Shares) || 0;
        const debtEquity = shares ? (debt / shares).toFixed(2) : '—';

        const set = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };

        set('roe', `${data.ROE || 0}%`);
        set('roce', `${data.ROCE || 0}%`);
        set('totalRevenue', revenue ? `₹${revenue.toLocaleString()}` : '—');
        set('netIncome', netIncome ? `₹${netIncome.toLocaleString()}` : '—');
        set('ebit', ebit ? `₹${ebit.toLocaleString()}` : '—');
        set('ocf', ocf ? `₹${ocf.toLocaleString()}` : '—');
        set('fcf', fcf ? `₹${fcf.toLocaleString()}` : '—');
        set('taxRate', `${(taxRate * 100).toFixed(2)}%`);
        set('debtToEquity', debtEquity);
        set('totalDebt', debt ? `₹${debt.toLocaleString()}` : '—');
        set('capex', capex ? `₹${capex.toLocaleString()}` : '—');
        set('da', da ? `₹${da.toLocaleString()}` : '—');
        set('shares', shares ? shares.toLocaleString() : '—');
    }

    // ===== FIXED: Growth mapping =====
    displayGrowth(data) {
        const set = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };

        set('revenueYoYGrowth', `${data['Revenue_YoY_Growth_%'] || 0}%`);
        set('profitYoYGrowth', `${data['Profit_YoY_Growth_%'] || 0}%`);
        set('cagrRevenue', `${data.CAGR_revenue || 0}%`);
        set('cagrNetIncome', `${data['Operating Margin'] || 0}%`);
        set('yearAnalyzed', data['Year Analyzed'] || '—');
        set('dateEnding', data['Date Ending'] || '—');
    }

    displayIntrinsicValue(data) {
        const price = Number(data['Current Price']) || 0;
        const intrinsic = Number(data['Intrinsic Value Per Share']) || 0;
        const margin = Number(data['Operating Margin']) || 0;
        const overUnder =
  price > intrinsic
    ? "Overvalued"
    : price < intrinsic
    ? "Undervalued"
    : "Fairly Valued";
        
        const set = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };
        
        set('marketPrice', price ? `₹${price}` : '—');
        set('intrinsicValue', intrinsic ? `₹${intrinsic}` : '—');
        set('marginOfSafety', `${margin}%`);
        set('overUnder', overUnder);
        
        // Set valuation status based on over/under
        const statusEl = document.getElementById('valuationStatus');
        if (statusEl) {
            if (overUnder === 'overvalued') {
                statusEl.textContent = 'Overvalued';
                statusEl.className = 'valuation-badge overvalued';
            } else if (overUnder === 'undervalued') {
                statusEl.textContent = 'Undervalued';
                statusEl.className = 'valuation-badge undervalued';
            } else {
                statusEl.textContent = 'Fairly Valued';
                statusEl.className = 'valuation-badge';
            }
        }
    }

    // ===== ENHANCED: Sentiment Display =====
    displaySentiment(data) {
        const sentiment = Number(data.Sentiment) || 0;
        
        const set = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };
        
        // Update sentiment gauge
        const gaugeFill = document.getElementById('sentimentGaugeFill');
        const gaugeValue = document.getElementById('sentimentGaugeValue');
        if (gaugeFill) {
            // Convert -1 to 1 range to 0-100% for gauge
            const percentage = ((sentiment + 1) / 2) * 100;
            gaugeFill.style.width = `${percentage}%`;
        }
        if (gaugeValue) gaugeValue.textContent = sentiment.toFixed(2);
        
        // Determine sentiment status and badge
        let status, badge, interpretation;
        if (sentiment > 0.6) {
            status = 'Positive';
            badge = 'Positive';
            interpretation = 'Market shows strong positive sentiment with favorable outlook';
        } else if (sentiment < 0.3) {
            status = 'Negative';
            badge = 'Negative';
            interpretation = 'Market shows negative sentiment with cautious outlook';
        } else {
            status = 'Neutral';
            badge = 'Neutral';
            interpretation = 'Market shows balanced sentiment with stable outlook';
        }
        
        // Update enhanced sentiment elements
        set('sentimentBadgeLarge', badge);
        set('sentimentStatus', status);
        set('sentimentInterpretation', interpretation);
        set('sentimentDescription', interpretation);
    }

    // ===== ENHANCED: Management Display =====
    displayManagement(data) {
        const ticker = data.Ticker;
        console.log("Displaying management for ticker:", ticker);
        console.log("Available management analysis data:", window.managementAnalysisData);

        const set = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        };
        
        // Initialize scores and reasons with fallback values
        let leadership = 0, capitalAllocation = 0, governance = 0;
        let communication = 0, stability = 0, marketTrust = 0;
        let leadershipReason = "", capitalAllocationReason = "", governanceReason = "";
        let communicationReason = "", stabilityReason = "", marketTrustReason = "";
        
        // Extract data from management analysis CSV based on Metric column
        if (window.managementAnalysisData && window.managementAnalysisData.length > 0) {
            console.log("Processing management analysis data...");
            
            window.managementAnalysisData.forEach(row => {
                const metric = row.Metric;
                const score = this.extractScore(row.Score) || 0;
                const reason = row.Reason || "";
                
                console.log(`Processing metric: ${metric}, score: ${score}, reason: ${reason}`);
                
                // Map metrics to variables
                switch(metric) {
                    case 'Leadership':
                        leadership = score;
                        leadershipReason = reason;
                        break;
                    case 'Capital Allocation':
                        capitalAllocation = score;
                        capitalAllocationReason = reason;
                        break;
                    case 'CapitalAllocation':
                        capitalAllocation = score;
                        capitalAllocationReason = reason;
                        break;
                    case 'Governance':
                        governance = score;
                        governanceReason = reason;
                        break;
                    case 'Communication':
                        communication = score;
                        communicationReason = reason;
                        break;
                    case 'Stability':
                        stability = score;
                        stabilityReason = reason;
                        break;
                    case 'Market Trust':
                        marketTrust = score;
                        marketTrustReason = reason;
                        break;
                    case 'MarketTrust':
                        marketTrust = score;
                        marketTrustReason = reason;
                        break;
                    case 'FinalManagementScore':
                        // This is overall score, not needed for individual metrics
                        break;
                }
            });
            
            console.log("Final leadership reason:", leadershipReason);
            console.log("Final capital allocation reason:", capitalAllocationReason);
            console.log("Final governance reason:", governanceReason);
        } else {
            console.log("No management analysis data available, using original data");
            
            // Fallback to original data if analysis data not found
            leadership = Number(data.Leadership) || 0;
            capitalAllocation = Number(data.CapitalAllocation) || 0;
            governance = Number(data.Governance) || 0;
            communication = Number(data.Communication) || 0;
            stability = Number(data.Stability) || 0;
            marketTrust = Number(data.MarketTrust) || 0;
        }
        
        // Update overall management score (convert to /10 scale)
        const overallScore = ((leadership + capitalAllocation + governance + communication + stability + marketTrust) / 6);
        set('managementScoreLarge', overallScore.toFixed(1));
        
        // Determine performance level
        let performanceLevel, summary;
        if (overallScore >= 8) {
            performanceLevel = 'Excellent';
            summary = 'Management demonstrates exceptional leadership and strategic direction with strong governance practices.';
        } else if (overallScore >= 6) {
            performanceLevel = 'Good';
            summary = 'Management shows solid performance with effective decision-making and operational capabilities.';
        } else if (overallScore >= 4) {
            performanceLevel = 'Average';
            summary = 'Management displays moderate performance with room for improvement in key areas.';
        } else {
            performanceLevel = 'Needs Improvement';
            summary = 'Management requires significant enhancement in leadership and operational effectiveness.';
        }
        
        set('performanceLevel', performanceLevel);
        set('managementSummaryText', summary);
        
        // Update individual management scores and append reasons
        const indicators = [
            { name: 'leadership', value: leadership, reason: leadershipReason },
            { name: 'capitalAllocation', value: capitalAllocation, reason: capitalAllocationReason },
            { name: 'governance', value: governance, reason: governanceReason },
            { name: 'communication', value: communication, reason: communicationReason },
            { name: 'stability', value: stability, reason: stabilityReason },
            { name: 'marketTrust', value: marketTrust, reason: marketTrustReason }
        ];
        
        indicators.forEach(indicator => {
            // Update score display
            set(`${indicator.name}Score`, `${indicator.value.toFixed(1)}/10`);
            
            // Update progress bar
            const barFill = document.getElementById(`${indicator.name}BarFill`);
            if (barFill) {
                barFill.style.width = `${(indicator.value / 10) * 100}%`;
            }
            
            // Append reason text to existing div (if reason exists)
            const reasonDiv = document.getElementById(`${indicator.name}Reason`);
            if (reasonDiv && indicator.reason && indicator.reason.trim()) {
                // Clear existing content first
                reasonDiv.innerHTML = "";
                
                // Create reason text element
                const reasonElement = document.createElement('div');
                reasonElement.className = 'management-reason';
                reasonElement.textContent = indicator.reason;
                
                // Append to existing reason div
                reasonDiv.appendChild(reasonElement);
                console.log(`✅ Appended reason to ${indicator.name}Reason: "${indicator.reason}"`);
            } else if (reasonDiv) {
                // Clear div if no reason exists
                reasonDiv.innerHTML = "";
                console.log(`⚠️ No reason text for ${indicator.name}, leaving div empty`);
            } else {
                console.log(`❌ Could not find div: ${indicator.name}Reason`);
            }
        });
    }
    
    extractScore(scoreString) {
        if (!scoreString) return 0;
        // Extract score from format like "0.8/10" or just "0.8"
        const match = scoreString.toString().match(/(\d+\.?\d*)/);
        return match ? parseFloat(match[1]) : 0;
    }
}

// ===== CSV LOADER =====
function loadAndPrintCSV() {
    return new Promise((resolve, reject) => {
        Papa.parse("result.csv", {
            download: true,
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
                const data2025 = results.data.filter(
                    r => Number(r["Year Analyzed"]) === 2024
                );
                window.companiesData2025 = data2025;
                console.log("Loaded 2025 rows:", data2025.length);
                resolve();   // ✅ tell await to continue
            },
            error: (err) => {
                console.error("CSV Load Failed:", err);
                reject(err);
            }
        });
    });
}

// ===== NEWS CSV LOADER =====
function loadNewsCSV() {
    return new Promise((resolve, reject) => {
        Papa.parse("COMPANY_sentiment_2024.csv", {
            download: true,
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
                window.companyNewsData = results.data;
                console.log("News CSV Loaded:", results.data.length);
                resolve();
            },
            error: (err) => reject(err)
        });
    });
}

// ===== MANAGEMENT ANALYSIS CSV LOADER =====
function loadManagementAnalysisCSV() {
    return new Promise((resolve, reject) => {
        Papa.parse("management_analysis_2024.csv", {
            download: true,
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
                window.managementAnalysisData = results.data;
                console.log("Management CSV Loaded:", results.data.length);
                resolve();
            },
            error: (err) => reject(err)
        });
    });
}
function initializeApp() {
    window.finova = new FinovaScreener();
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});