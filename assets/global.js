/**
 * global.js — native-real.com 共通スクリプト
 * global-design.css と同様、全ページで読み込む。
 */

/* ── フローティング報告ボタン ── */
(function(){
  // feedbackページ自体には表示しない
  if(location.pathname.indexOf('/feedback') === 0) return;

  var a = document.createElement('a');
  a.href = '/feedback/';
  a.className = 'fb-float';
  a.setAttribute('aria-label', '問題を報告');
  a.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg><span>問題を報告</span>';
  document.body.appendChild(a);

  // スクロールして少し経ってから表示（すぐ出すと邪魔）
  var shown = false;
  window.addEventListener('scroll', function(){
    if(!shown && window.scrollY > 300){
      a.classList.add('visible');
      shown = true;
    }
  });
  // 5秒後にも表示（スクロールしないページ対策）
  setTimeout(function(){
    if(!shown){
      a.classList.add('visible');
      shown = true;
    }
  }, 5000);
})();
