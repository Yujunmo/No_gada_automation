(function () {
    var container = document.getElementById('page-impact-analysis');
    if (!container) return;

    container.innerHTML = `
        <div class="header">
            <div class="badge">영향도 분석</div>
            <h1>Impact Analysis</h1>
            <p>테이블명을 입력하면 그 테이블을 참조하는 DBIO를 찾습니다.<br>DBIO를 펼치면 연결된 비즈·서비스·배치 모듈을 조회하고, 비즈모듈은 다시 펼쳐 그 비즈를 부르는 상위 모듈을 계속 따라갈 수 있습니다(서비스·배치는 항상 최상위).</p>
        </div>

        <form class="ia-search-bar" id="ia-search-form">
            <select id="ia-target-type" class="ia-search-select">
                <option value="table">테이블</option>
                <option value="biz">비즈모듈</option>
            </select>
            <div class="ia-combo" id="ia-prog-combo" style="display:none;">
                <input type="text" id="ia-prog" class="ia-combo-input" placeholder="업무그룹" autocomplete="off">
                <ul id="ia-prog-list" class="ia-combo-list"></ul>
            </div>
            <input type="text" id="ia-search-input" placeholder="테이블명을 입력하세요 (예: PFO_FUND_BS)" autocomplete="off">
            <button type="submit" class="ia-search-btn" id="ia-search-btn">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <circle cx="11" cy="11" r="6.5"/>
                    <path stroke-linecap="round" d="M20 20l-4.3-4.3"/>
                </svg>
                <span>검색</span>
            </button>
        </form>
    `;

    var form = container.querySelector('#ia-search-form');
    var typeSel = container.querySelector('#ia-target-type');
    var searchInput = container.querySelector('#ia-search-input');
    var progCombo = container.querySelector('#ia-prog-combo');
    var progInput = container.querySelector('#ia-prog');
    var progList = container.querySelector('#ia-prog-list');
    var PLACEHOLDER = {
        table: '테이블명을 입력하세요 (예: PFO_FUND_BS)',
        biz: '비즈모듈명을 입력하세요 (예: MZPFM_FundInfoSave)',
    };
    // Table Extractor와 동일한 업무그룹 코드
    var PROG_OPTIONS = ['PCSP', 'PCSH', 'NCOM', 'NCSP', 'PCOM', 'PPFR', 'RLGR'];

    // 비즈모듈 조회는 업무그룹이 필요하지만 테이블 조회는 필요 없다.
    function updateProgVisibility() {
        progCombo.style.display = typeSel.value === 'biz' ? '' : 'none';
    }

    function renderProgList(query) {
        var q = (query || '').trim().toUpperCase();
        var matches = PROG_OPTIONS.filter(function (p) {
            return p.indexOf(q) !== -1;
        });
        if (!matches.length) {
            progList.innerHTML = '';
            progList.classList.remove('open');
            return;
        }
        progList.innerHTML = matches.map(function (p) {
            return '<li data-value="' + p + '">' + p + '</li>';
        }).join('');
        progList.classList.add('open');
    }

    typeSel.addEventListener('change', function () {
        searchInput.placeholder = PLACEHOLDER[typeSel.value];
        updateProgVisibility();
    });

    progInput.addEventListener('input', function () {
        renderProgList(progInput.value);
    });

    progInput.addEventListener('focus', function () {
        renderProgList(progInput.value);
    });

    // mousedown은 input의 blur보다 먼저 발생하므로 클릭 선택에 사용
    progList.addEventListener('mousedown', function (e) {
        var li = e.target.closest('li');
        if (!li) return;
        progInput.value = li.getAttribute('data-value');
        progList.classList.remove('open');
    });

    progInput.addEventListener('blur', function () {
        progList.classList.remove('open');
    });

    form.addEventListener('submit', function (e) {
        e.preventDefault();
    });
}());
