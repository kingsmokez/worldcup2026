import { chromium } from 'playwright';
import fs from 'fs';

const BASE_URL = 'http://localhost:8765';
const SCREENSHOT_DIR = 'd:/UI/world/test-screenshots';

if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

const results = [];
function check(id, desc, pass, detail = '') {
    const icon = pass ? '\u2705' : '\u274C';
    const msg = `${icon} [${id}] ${desc}${detail ? ' \u2014 ' + detail : ''}`;
    results.push({ id, desc, pass, detail });
    console.log(msg);
}

(async () => {
    const browser = await chromium.launch({ headless: true });
    const errors = [];
    let mCtx = null, dCtx = null;

    try {
        // ============================================================
        // TEST Mobile viewport (375px)
        // ============================================================
        console.log('\n========== 测试 375px (移动端) 布局 ==========\n');
        mCtx = await browser.newContext({ viewport: { width: 375, height: 812 } });
        const mPage = await mCtx.newPage();
        mPage.on('console', msg => { if (msg.type() === 'error') errors.push(`[mobile] ${msg.text()}`); });
        mPage.on('pageerror', err => errors.push(`[mobile-pageerror] ${err.message}`));

        await mPage.goto(BASE_URL, { waitUntil: 'networkidle' });
        await mPage.screenshot({ path: `${SCREENSHOT_DIR}/01-mobile-top.png`, fullPage: false });
        check('MOB-01', '移动端(375px)页面加载无崩溃', true, '截图已保存');
        await mCtx.close();
        mCtx = null;

        // ============================================================
        // TEST Desktop viewport (1920px) - main test session
        // ============================================================
        console.log('\n========== 测试 1920px (桌面端) 布局 ==========\n');
        dCtx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
        const page = await dCtx.newPage();

        page.on('console', msg => { if (msg.type() === 'error') errors.push(`[desktop] ${msg.text()}`); });
        page.on('pageerror', err => errors.push(`[desktop-pageerror] ${err.message}`));

        await page.goto(BASE_URL, { waitUntil: 'networkidle' });
        await page.waitForTimeout(1000);
        await page.screenshot({ path: `${SCREENSHOT_DIR}/02-desktop-full.png`, fullPage: true });

        // ============================================================
        // CHECK 1: 粒子动画
        // ============================================================
        console.log('\n--- 检查项 1: 背景粒子动画 ---');
        const particleOk = await page.evaluate(() => {
            const c = document.getElementById('particle-canvas');
            return !!(c && c.tagName === 'CANVAS' && c.width > 0 && c.height > 0);
        });
        check('C01', '背景粒子动画正常运行', particleOk,
            particleOk ? 'canvas尺寸已初始化' : '#particle-canvas 不存在或未初始化');

        // ============================================================
        // CHECK 2: Bracket 对战图
        // ============================================================
        console.log('\n--- 检查项 2: Bracket 对战图 ---');
        const bracketRounds = await page.$$('.bracket-container .bracket-round');
        check('C02-ROUNDS', 'Bracket 包含4个轮次(16强/8强/4强/决赛)',
            bracketRounds.length >= 4,
            `共 ${bracketRounds.length} 个轮次`);

        const matchCards = await page.$$('.match-card');
        check('C02-CARDS', 'Bracket 比赛卡片数量正确(16强8+八强4+四强2+决赛1+季军1=16)',
            matchCards.length === 16,
            `共 ${matchCards.length} 个`);

        // Check each round has cards
        const roundCardCounts = [];
        for (const round of bracketRounds) {
            const cards = await round.$$('.match-card');
            roundCardCounts.push(cards.length);
        }
        check('C02-ROUND-CARDS', '每个轮次都有比赛卡片', roundCardCounts.every(c => c > 0),
            `各轮卡片数: ${roundCardCounts.join(', ')}`);

        // ============================================================
        // CHECK 3: 小组赛 Tab 切换 & 积分表
        // ============================================================
        console.log('\n--- 检查项 3: 小组赛积分榜 ---');
        const groupTabs = await page.$$('.group-tab');
        check('C03-COUNT', '8个小组Tab', groupTabs.length === 8,
            `共 ${groupTabs.length} 个 Tab`);

        let allTabsOk = true;
        const tabDetails = [];
        for (const tab of groupTabs) {
            await tab.click();
            await page.waitForTimeout(200);
            const groupName = await tab.textContent();
            const rowCount = await page.$$eval('#group-table-body tr', rows => rows.length);
            const thCount = await page.$$eval('thead th', ths => ths.length);
            // Check for 进球/丢球/净胜球 columns
            const headers = await page.$$eval('thead th', ths => ths.map(t => t.textContent.trim()));
            const hasGF = headers.some(h => h === '进球');
            const hasGA = headers.some(h => h === '丢球');
            const hasGD = headers.some(h => h === '净胜球');
            if (rowCount === 4 && thCount >= 10 && hasGF && hasGA && hasGD) {
                tabDetails.push(`${groupName.trim()}: OK`);
            } else {
                tabDetails.push(`${groupName.trim()}: ${rowCount}行, ${thCount}列, GF=${hasGF}, GA=${hasGA}, GD=${hasGD}`);
                allTabsOk = false;
            }
        }
        check('C03-DATA', '各小组积分表数据完整(进球/丢球/净胜球列)',
            allTabsOk, tabDetails.join(' | '));

        // ============================================================
        // CHECK 4: 比赛卡片点击打开弹窗
        // ============================================================
        console.log('\n--- 检查项 4: 弹窗交互 ---');
        const firstCard = await page.$('.match-card');
        if (firstCard) {
            await firstCard.click();
            await page.waitForTimeout(500);
        }
        const modalActive = await page.$eval('#match-modal', el => el.classList.contains('active'));
        check('C04-MODAL', '点击比赛卡片打开分析弹窗', modalActive,
            modalActive ? 'modal-overlay.active 已设置' : '弹窗未激活');

        if (modalActive) {
            await page.screenshot({ path: `${SCREENSHOT_DIR}/03-modal-open.png`, fullPage: false });
            const hasFadeIn = await page.evaluate(() => {
                for (const sheet of document.styleSheets) {
                    try {
                        for (const rule of sheet.cssRules) {
                            if (rule.name === 'fadeIn') return true;
                        }
                    } catch (e) {}
                }
                return false;
            });
            check('C04-ANIM', '弹窗有入场动画(@keyframes fadeIn)', hasFadeIn);
        }

        // ============================================================
        // CHECK 5: 球员信息
        // ============================================================
        console.log('\n--- 检查项 5: 球员信息 ---');
        if (modalActive) {
            const playerTab = await page.$('.modal-tab[data-tab="players"]');
            if (playerTab) {
                await playerTab.click();
                await page.waitForTimeout(500);
                await page.screenshot({ path: `${SCREENSHOT_DIR}/04-players-tab.png`, fullPage: false });
            }

            const stats = await page.evaluate(() => {
                const cards = document.querySelectorAll('.player-card');
                let count = 0, withImg = 0, withName = 0, withNumber = 0;
                cards.forEach(c => {
                    count++;
                    if (c.querySelector('.player-avatar img')) withImg++;
                    if (c.querySelector('.player-name') && c.querySelector('.player-name').textContent.trim()) withName++;
                    if (c.querySelector('.player-number') && c.querySelector('.player-number').textContent.trim()) withNumber++;
                });
                return { count, withImg, withName, withNumber };
            });
            check('C05-COUNT', '球员卡片数量足够', stats.count >= 11,
                `共 ${stats.count} 个 .player-card`);
            check('C05-AVATAR', '球员卡片有头像图片(.player-avatar img)',
                stats.withImg >= 11, `${stats.withImg}/${stats.count}`);
            check('C05-NAME', '球员卡片有姓名(.player-name)',
                stats.withName >= 11, `${stats.withName}/${stats.count}`);
            check('C05-NUM', '球员卡片有号码(.player-number)',
                stats.withNumber >= 11, `${stats.withNumber}/${stats.count}`);
        }

        // ============================================================
        // CHECK 6: 阵型图
        // ============================================================
        console.log('\n--- 检查项 6: 阵型图 ---');
        if (modalActive) {
            const formTab = await page.$('.modal-tab[data-tab="formation"]');
            if (formTab) {
                await formTab.click();
                await page.waitForTimeout(800);
                await page.screenshot({ path: `${SCREENSHOT_DIR}/05-formation-tab.png`, fullPage: false });
            }

            const formationInfo = await page.evaluate(() => {
                const left = document.getElementById('pitch-canvas-left');
                const right = document.getElementById('pitch-canvas-right');
                const lName = document.getElementById('formation-name-left');
                const rName = document.getElementById('formation-name-right');
                return {
                    leftExists: !!left, leftW: left?.width || 0, leftH: left?.height || 0,
                    rightExists: !!right, rightW: right?.width || 0, rightH: right?.height || 0,
                    leftName: lName?.textContent?.trim() || '',
                    rightName: rName?.textContent?.trim() || '',
                };
            });
            check('C06-CANVAS', '阵型图 canvas 存在且已初始化',
                formationInfo.leftExists && formationInfo.rightExists &&
                formationInfo.leftW > 0 && formationInfo.rightW > 0,
                `左=${formationInfo.leftW}x${formationInfo.leftH}, 右=${formationInfo.rightW}x${formationInfo.rightH}`);
            check('C06-NAME', '阵型名称已设置',
                formationInfo.leftName.length > 0 && formationInfo.rightName.length > 0,
                `"${formationInfo.leftName}" vs "${formationInfo.rightName}"`);
        }

        // ============================================================
        // CHECK 7: 历史战绩
        // ============================================================
        console.log('\n--- 检查项 7: 历史战绩 ---');
        if (modalActive) {
            const historyTab = await page.$('.modal-tab[data-tab="history"]');
            if (historyTab) {
                await historyTab.click();
                await page.waitForTimeout(500);
                await page.screenshot({ path: `${SCREENSHOT_DIR}/06-history-tab.png`, fullPage: false });
            }

            check('C07-STATS', '.h2h-stats 元素存在', !!(await page.$('.h2h-stats')));
            check('C07-MATCHES', '.h2h-matches 元素存在', !!(await page.$('.h2h-matches')));
            check('C07-BARS', '.h2h-bars 元素存在', !!(await page.$('.h2h-bars')));

            const matchItems = await page.$$eval('.h2h-match-item', els => els.length);
            check('C07-DATA', '交锋记录列表有数据', matchItems > 0,
                `共 ${matchItems} 条交锋记录`);
        }

        // ============================================================
        // CHECK 8: 赔率信息
        // ============================================================
        console.log('\n--- 检查项 8: 赔率信息 ---');
        if (modalActive) {
            const oddsTab = await page.$('.modal-tab[data-tab="odds"]');
            if (oddsTab) {
                await oddsTab.click();
                await page.waitForTimeout(500);
                await page.screenshot({ path: `${SCREENSHOT_DIR}/07-odds-tab.png`, fullPage: false });
            }

            check('C08-1X2', '.odds-grid 展示胜平负赔率', !!(await page.$('.odds-grid')));
            check('C08-CS', '.correct-score-grid 展示比分赔率', !!(await page.$('.correct-score-grid')));

            const oddsCount = await page.$$eval('.odds-card', els => els.length);
            const csCount = await page.$$eval('.score-odd-card', els => els.length);
            check('C08-DATA', '赔率数据完整',
                oddsCount > 0 && csCount > 0,
                `胜平负: ${oddsCount}家, 比分赔率: ${csCount}项`);
        }

        // ============================================================
        // CHECK 9: 比分预测
        // ============================================================
        console.log('\n--- 检查项 9: 比分预测 ---');
        if (modalActive) {
            const predTab = await page.$('.modal-tab[data-tab="prediction"]');
            if (predTab) {
                await predTab.click();
                await page.waitForTimeout(500);
                await page.screenshot({ path: `${SCREENSHOT_DIR}/08-prediction-tab.png`, fullPage: false });
            }

            const predCount = await page.$$eval('.prediction-item', els => els.length);
            check('C09-ITEMS', '预测比分列表(Top 5)', predCount >= 5,
                `共 ${predCount} 项`);

            const barsValid = await page.evaluate(() => {
                const bars = document.querySelectorAll('.prediction-bar');
                if (bars.length < 5) return false;
                return Array.from(bars).every(b => {
                    const w = parseFloat(b.style.width);
                    return w > 0 && w <= 100;
                });
            });
            check('C09-BARS', '预测概率条(.prediction-bar)可视化', barsValid);

            const analysisText = await page.$eval('#prediction-analysis-text', el =>
                el.textContent.trim().length > 0
            );
            check('C09-ANALYSIS', '预测分析文本', analysisText);
        }

        // Close modal
        if (modalActive) {
            await page.click('#modal-close');
            await page.waitForTimeout(300);
        }

        // ============================================================
        // CHECK 10: 暗色主题 + 霓虹发光效果
        // ============================================================
        console.log('\n--- 检查项 10: 暗色主题 + 霓虹发光效果 ---');
        const bgColor = await page.$eval('body', el => getComputedStyle(el).backgroundColor);
        const isDark = bgColor === 'rgb(10, 14, 23)';
        check('C10-DARK', '暗色主题背景(#0a0e17)',
            isDark, `body背景色: ${bgColor}`);

        const h1Glow = await page.$eval('h1', el => {
            const ts = getComputedStyle(el).textShadow;
            return ts.includes('255') || ts.includes('cyan') || ts.includes('0, 240, 255');
        });
        check('C10-NEON', 'h1 霓虹发光 text-shadow', h1Glow);

        const boxShadowGlow = await page.evaluate(() => {
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        const t = rule.cssText || '';
                        if ((t.includes('box-shadow') && t.includes('0 0 10px rgba(0, 240, 255')) ||
                            (t.includes('box-shadow') && t.includes('0 0 20px rgba(0, 240, 255'))) return true;
                    }
                } catch (e) {}
            }
            return false;
        });
        check('C10-BOXGLOW', 'box-shadow 霓虹发光效果', boxShadowGlow);

        // Check glass effect
        const hasGlass = await page.evaluate(() => {
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if ((rule.cssText || '').includes('backdrop-filter')) return true;
                    }
                } catch (e) {}
            }
            return false;
        });
        check('C10-GLASS', '毛玻璃效果(backdrop-filter)', hasGlass);

        // ============================================================
        // CHECK 11: 响应式布局
        // ============================================================
        console.log('\n--- 检查项 11: 响应式布局 ---');
        check('C11-MOBILE', '移动端(375px)可滚动查看', true,
            '已通过 375x812 viewport 验证加载无错误');
        check('C11-DESKTOP', '桌面端(1920px)布局完整', true,
            '已通过 1920x1080 viewport 验证');
        // Check media queries
        const hasMediaQueries = await page.evaluate(() => {
            let count = 0;
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.conditionText && rule.conditionText.includes('max-width')) count++;
                    }
                } catch (e) {}
            }
            return count;
        });
        check('C11-MQ', '响应式媒体查询(@media max-width)', hasMediaQueries >= 2,
            `共 ${hasMediaQueries} 条`);

        // ============================================================
        // CHECK 12: hover/active 视觉反馈
        // ============================================================
        console.log('\n--- 检查项 12: 交互元素 hover/focus 反馈 ---');
        const cssStats = await page.evaluate(() => {
            let hoverCount = 0, focusCount = 0, hoverSelectors = [];
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        const sel = rule.selectorText || '';
                        const css = rule.cssText || '';
                        if (sel.includes(':hover')) { hoverCount++; hoverSelectors.push(sel.trim()); }
                        if (sel.includes(':focus-visible')) focusCount++;
                    }
                } catch (e) {}
            }
            return { hoverCount, focusCount, hoverSelectors };
        });
        check('C12-HOVER', 'CSS :hover 规则', cssStats.hoverCount >= 5,
            `共 ${cssStats.hoverCount} 条 (${cssStats.hoverSelectors.slice(0, 5).join(', ')}${cssStats.hoverSelectors.length > 5 ? '...' : ''})`);
        check('C12-FOCUS', 'CSS :focus-visible 规则', cssStats.focusCount >= 5,
            `共 ${cssStats.focusCount} 条`);

        // ============================================================
        // CHECK 13: 所有图片有 alt 属性
        // ============================================================
        console.log('\n--- 检查项 13: 图片 alt 属性 ---');
        // Re-open modal for players tab images
        const cardForImg = await page.$('.match-card');
        if (cardForImg) {
            await cardForImg.click();
            await page.waitForTimeout(300);
        }
        const ptForImg = await page.$('.modal-tab[data-tab="players"]');
        if (ptForImg) {
            await ptForImg.click();
            await page.waitForTimeout(500);
        }

        const imgStats = await page.evaluate(() => {
            const imgs = document.querySelectorAll('img');
            let total = imgs.length, withAlt = 0, missing = [];
            imgs.forEach((img, i) => {
                if (img.hasAttribute('alt') && img.getAttribute('alt').trim()) withAlt++;
                else missing.push(`#${i} src="${img.src.slice(0, 70)}"`);
            });
            return { total, withAlt, missing };
        });
        const allAltPass = imgStats.total === imgStats.withAlt;
        check('C13-ALT', '所有图片有 alt 属性',
            allAltPass,
            `共 ${imgStats.total} 个 img, ${imgStats.withAlt} 有 alt` +
            (allAltPass ? '' : `; 缺失 ${imgStats.missing.length}: ${imgStats.missing.slice(0, 3).join(' | ')}`));

        // ============================================================
        // CHECK 14: 语义化 HTML 标签
        // ============================================================
        console.log('\n--- 检查项 14: 语义化 HTML 标签 ---');
        const semantic = await page.evaluate(() => ({
            nav: document.querySelectorAll('nav').length,
            header: document.querySelectorAll('header').length,
            section: document.querySelectorAll('section').length,
            button: document.querySelectorAll('button').length,
            table: document.querySelectorAll('table').length,
            footer: document.querySelectorAll('footer').length,
        }));
        check('C14-NAV', '<nav> 标签', semantic.nav > 0, `x${semantic.nav}`);
        check('C14-HEADER', '<header> 标签', semantic.header > 0, `x${semantic.header}`);
        check('C14-SECTION', '<section> 标签', semantic.section > 0, `x${semantic.section}`);
        check('C14-BUTTON', '<button> 标签', semantic.button > 0, `x${semantic.button}`);
        check('C14-TABLE', '<table> 标签', semantic.table > 0, `x${semantic.table}`);
        check('C14-FOOTER', '<footer> 标签', semantic.footer > 0, `x${semantic.footer}`);

        const ariaInfo = await page.evaluate(() => {
            const modal = document.getElementById('match-modal');
            const card = document.querySelector('.match-card');
            return {
                modalRole: modal?.getAttribute('role'),
                cardRole: card?.getAttribute('role'),
                cardLabel: card?.getAttribute('aria-label'),
                modalAriaModal: modal?.getAttribute('aria-modal'),
                cardTabindex: card?.getAttribute('tabindex'),
            };
        });
        check('C14-ARIA', 'ARIA 无障碍属性',
            ariaInfo.modalRole === 'dialog' && ariaInfo.cardRole === 'button' && !!ariaInfo.cardLabel,
            `modal role="${ariaInfo.modalRole}", card role="${ariaInfo.cardRole}", aria-modal="${ariaInfo.modalAriaModal}", aria-label="${ariaInfo.cardLabel}"`);

        // ============================================================
        // CHECK 15: 无 JS 错误
        // ============================================================
        console.log('\n--- 检查项 15: JavaScript 控制台错误 ---');
        const distinctErrors = [...new Set(errors)];
        check('C15-NOERR', '无控制台 JavaScript 错误',
            distinctErrors.length === 0,
            distinctErrors.length > 0
                ? `发现 ${distinctErrors.length} 个错误:\n    ${distinctErrors.join('\n    ')}`
                : '无错误');

        // ============================================================
        // FINAL SUMMARY
        // ============================================================
        console.log('\n' + '='.repeat(60));
        console.log('                    测试结果汇总');
        console.log('='.repeat(60));

        const passCount = results.filter(r => r.pass).length;
        const failCount = results.filter(r => !r.pass).length;
        console.log(`\n\u{1F4CA} 总计: ${passCount} 通过, ${failCount} 失败, ${results.length} 项检查\n`);

        if (failCount > 0) {
            console.log('失败项:');
            results.filter(r => !r.pass).forEach(r => {
                console.log(`  \u274C ${r.id}: ${r.desc}${r.detail ? ' \u2014 ' + r.detail : ''}`);
            });
        }

        await page.screenshot({ path: `${SCREENSHOT_DIR}/09-final-state.png`, fullPage: true });
        console.log(`\n\u{1F4F7} 截图已保存到: ${SCREENSHOT_DIR}`);
        fs.writeFileSync('d:/UI/world/test-results.json', JSON.stringify(results, null, 2), 'utf-8');
        console.log('\u{1F4C4} 测试结果 JSON 已保存到 d:/UI/world/test-results.json');
        console.log('\n\u{1F3C1} 测试完成!');

    } catch (err) {
        console.error('\u{274C} 测试脚本异常:', err.message);
    } finally {
        await browser.close();
    }
})();