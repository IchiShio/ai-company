// ============================================================
// native-real.com SEO Data Collector
// Account: ichieigo7@gmail.com
// Saves CSVs to Google Drive: GoogleG4,SearchConsole/YYYY-MM-DD/
// ============================================================

const CONFIG = {
  SC_PROPERTY:      'https://native-real.com/',
  GA4_PROPERTY_ID:  '525926980',
  DRIVE_FOLDER_ID:  '1UsvXavXHcvX8W95iAu0p-jJnrRyyZ-0l', // GoogleG4,SearchConsole フォルダ
  TIMEZONE:         'Asia/Tokyo',
  DAYS:             28,
};

// ============================================================
// メイン（タイムトリガーから呼び出す）
// ============================================================

function collectSEOData() {
  const today    = new Date();
  const dateStr  = formatDate(today);
  const log      = [];

  const folder = getOrCreateFolder(CONFIG.DRIVE_FOLDER_ID, dateStr);

  collectSearchConsole(folder, log);
  collectGA4(folder, log);

  const logText =
    `実行日時: ${dateStr}\n取得結果:\n` +
    log.map(r => '  - ' + r).join('\n');
  saveFile(folder, 'collection_log.txt', logText);

  Logger.log(logText);
}

// ============================================================
// Search Console（5次元）
// ============================================================

function collectSearchConsole(folder, log) {
  const { startDate, endDate } = getDateRange();
  const token   = ScriptApp.getOAuthToken();
  const baseUrl = 'https://searchconsole.googleapis.com/webmasters/v3/sites/' +
                  encodeURIComponent(CONFIG.SC_PROPERTY) + '/searchAnalytics/query';

  const datasets = [
    { file: 'queries.csv',   dim: 'query',   limit: 5000, col: '上位のクエリ'   },
    { file: 'pages.csv',     dim: 'page',    limit: 5000, col: '上位のページ'   },
    { file: 'dates.csv',     dim: 'date',    limit: 28,   col: '日付'          },
    { file: 'devices.csv',   dim: 'device',  limit: 10,   col: 'デバイス'      },
    { file: 'countries.csv', dim: 'country', limit: 250,  col: '国'            },
  ];

  for (const ds of datasets) {
    try {
      const res = UrlFetchApp.fetch(baseUrl, {
        method:           'POST',
        headers:          { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
        payload:          JSON.stringify({ startDate, endDate, dimensions: [ds.dim], rowLimit: ds.limit }),
        muteHttpExceptions: true,
      });

      const json = JSON.parse(res.getContentText());
      if (json.error) throw new Error(json.error.message);

      const header = [ds.col, 'クリック数', '表示回数', 'CTR', '掲載順位'];
      const rows   = (json.rows || []).map(r => [
        r.keys[0],
        r.clicks,
        r.impressions,
        (r.ctr * 100).toFixed(2) + '%',
        r.position.toFixed(1),
      ]);

      saveCsv(folder, ds.file, header, rows);
      log.push('SC ' + ds.dim + ': 成功 (' + rows.length + '行)');
    } catch (e) {
      log.push('SC ' + ds.dim + ': エラー - ' + e.message);
    }
  }
}

// ============================================================
// GA4（トラフィック獲得 + ページとスクリーン）
// ============================================================

function collectGA4(folder, log) {
  const token = ScriptApp.getOAuthToken();
  const url   = 'https://analyticsdata.googleapis.com/v1beta/properties/' +
                CONFIG.GA4_PROPERTY_ID + ':runReport';

  // --- トラフィック獲得 → ga4_traffic.csv ---
  try {
    const res  = UrlFetchApp.fetch(url, {
      method:  'POST',
      headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
      payload: JSON.stringify({
        dimensions:  [{ name: 'sessionDefaultChannelGroup' }],
        metrics: [
          { name: 'sessions' },
          { name: 'engagedSessions' },
          { name: 'userEngagementDuration' },
          { name: 'engagementRate' },
        ],
        dateRanges: [{ startDate: '28daysAgo', endDate: 'today' }],
        limit: 20,
      }),
      muteHttpExceptions: true,
    });

    const json = JSON.parse(res.getContentText());
    if (json.error) throw new Error(json.error.message);

    const header = [
      'セッションのメインのチャネル グループ',
      'セッション',
      'エンゲージのあったセッション数',
      'ユーザーエンゲージメント（秒）',
      'エンゲージメント率',
    ];
    const rows = (json.rows || []).map(r => [
      r.dimensionValues[0].value,
      r.metricValues[0].value,
      r.metricValues[1].value,
      parseFloat(r.metricValues[2].value).toFixed(1),
      parseFloat(r.metricValues[3].value).toFixed(4),
    ]);

    saveCsv(folder, 'ga4_traffic.csv', header, rows);
    log.push('GA4 traffic: 成功 (' + rows.length + '行)');
  } catch (e) {
    log.push('GA4 traffic: エラー - ' + e.message);
  }

  // --- ページとスクリーン → ga4_pages.csv ---
  try {
    const res  = UrlFetchApp.fetch(url, {
      method:  'POST',
      headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
      payload: JSON.stringify({
        dimensions: [{ name: 'pagePath' }, { name: 'pageTitle' }],
        metrics: [
          { name: 'screenPageViews' },
          { name: 'activeUsers' },
          { name: 'userEngagementDuration' },
          { name: 'engagementRate' },
        ],
        dateRanges: [{ startDate: '28daysAgo', endDate: 'today' }],
        orderBys:   [{ metric: { metricName: 'screenPageViews' }, desc: true }],
        limit: 100,
      }),
      muteHttpExceptions: true,
    });

    const json = JSON.parse(res.getContentText());
    if (json.error) throw new Error(json.error.message);

    // 平均エンゲージメント時間（秒/ユーザー）を計算して保存
    const header = [
      'ページのパスとスクリーン クラス',
      'ページ タイトルとスクリーン名',
      'ページビュー数',
      'アクティブ ユーザー数',
      '平均エンゲージメント時間（秒）',
      'エンゲージメント率',
    ];
    const rows = (json.rows || []).map(r => {
      const users    = parseInt(r.metricValues[1].value) || 1;
      const totalSec = parseFloat(r.metricValues[2].value);
      const avgSec   = (totalSec / users).toFixed(1);
      return [
        r.dimensionValues[0].value,
        r.dimensionValues[1].value,
        r.metricValues[0].value,
        r.metricValues[1].value,
        avgSec,
        parseFloat(r.metricValues[3].value).toFixed(4),
      ];
    });

    saveCsv(folder, 'ga4_pages.csv', header, rows);
    log.push('GA4 pages: 成功 (' + rows.length + '行)');
  } catch (e) {
    log.push('GA4 pages: エラー - ' + e.message);
  }
}

// ============================================================
// ユーティリティ
// ============================================================

function getDateRange() {
  const end   = new Date();
  const start = new Date(end.getTime() - CONFIG.DAYS * 24 * 60 * 60 * 1000);
  return { startDate: formatDate(start), endDate: formatDate(end) };
}

function formatDate(date) {
  return Utilities.formatDate(date, CONFIG.TIMEZONE, 'yyyy-MM-dd');
}

function getOrCreateFolder(parentId, name) {
  const parent   = DriveApp.getFolderById(parentId);
  const existing = parent.getFoldersByName(name);
  return existing.hasNext() ? existing.next() : parent.createFolder(name);
}

function saveCsv(folder, filename, header, rows) {
  const lines = [header.map(csvEscape).join(',')];
  for (const row of rows) {
    lines.push(row.map(csvEscape).join(','));
  }
  saveFile(folder, filename, '\uFEFF' + lines.join('\n')); // BOM付き UTF-8
}

function csvEscape(cell) {
  const s = String(cell);
  return s.includes(',') || s.includes('"') || s.includes('\n')
    ? '"' + s.replace(/"/g, '""') + '"'
    : s;
}

function saveFile(folder, filename, content) {
  const existing = folder.getFilesByName(filename);
  if (existing.hasNext()) {
    existing.next().setContent(content);
  } else {
    folder.createFile(filename, content, MimeType.PLAIN_TEXT);
  }
}
