(function () {
    var container = document.getElementById('page-table-extractor');
    if (!container) return;

    container.innerHTML = `
        <div class="header">
            <div class="badge">테이블 추출 및 이관 도구</div>
            <h1>Table Extractor</h1>
            <p>서비스 ID 또는 DBIO ID를 입력하면 참조하는 모든 테이블을 추출합니다.<br>현재 프로시저 내부의 테이블의 추출 기능은 지원하지 않습니다.</p>
            
        </div>

        <div class="extractor-controls">
            <select id="te-id-type">
                <option value="dbio">DBIO</option>
                <option value="service">Service</option>
                <option value="batch">Batch</option>
                <option value="biz">Biz</option>
            </select>
            <div class="te-combo" id="te-prog-combo">
                <input type="text" id="te-prog" class="te-combo-input" placeholder="업무그룹" autocomplete="off">
                <ul id="te-prog-list" class="te-combo-list"></ul>
            </div>
            <input type="text" id="te-id-input" placeholder="DBIO ID를 입력하세요 (여러 개는 쉼표로 구분해 입력하세요)">
            <button id="te-submit">추출하기</button>
            <button id="te-settings-btn" class="te-icon-btn" title="설정" aria-label="설정">&#8942;</button>
        </div>

        <div class="extractor-workspace">
            <div class="card te-panel">
                <div class="te-panel-title">추출된 테이블</div>
                <div id="te-result" class="te-result">
                    <div class="te-empty">추출된 테이블이 여기에 표시됩니다.</div>
                </div>
            </div>
            <div class="card te-panel">
                <div class="te-panel-title">이관 sql</div>
                <div id="te-keyin" class="te-keyin">
                    <div class="te-empty">테이블을 추출·선택하면 PK 입력란이 표시됩니다.</div>
                </div>
                <div class="te-gen-bar">
                    <label class="te-gen-field">
                        <span class="te-gen-label">from link</span>
                        <input type="text" id="te-from-link" class="te-dblink-input" placeholder="FROM 링크(원격 소스)" value="@dl_patru_Trups" autocomplete="off">
                    </label>
                    <label class="te-gen-field">
                        <span class="te-gen-label">to link</span>
                        <input type="text" id="te-to-link" class="te-dblink-input" placeholder="TO 링크(대상, 비우면 로컬)" value="@dl_datru_truds" autocomplete="off">
                    </label>
                    <button id="te-generate" class="btn-secondary">이관 SQL 생성</button>
                </div>
                <div class="te-keyin-hint">생성 버튼을 누르면 이관 SQL이 팝업으로 표시됩니다.</div>
            </div>
        </div>

        <div id="te-modal" class="te-modal-overlay" style="display:none;">
            <div class="te-modal" role="dialog" aria-modal="true">
                <div class="te-modal-head">
                    <span class="te-modal-title">이관 SQL</span>
                    <div class="te-modal-head-actions">
                        <button id="te-modal-copy-all" class="btn-secondary">전체 복사</button>
                        <button id="te-modal-close" class="te-modal-x" title="닫기" aria-label="닫기">&times;</button>
                    </div>
                </div>
                <div id="te-modal-body" class="te-modal-body"></div>
            </div>
        </div>

        <div id="te-settings-modal" class="te-modal-overlay" style="display:none;">
            <div class="te-modal te-settings-modal" role="dialog" aria-modal="true">
                <div class="te-modal-head">
                    <span class="te-modal-title">설정</span>
                    <div class="te-modal-head-actions">
                        <button id="te-settings-close" class="te-modal-x" title="닫기" aria-label="닫기">&times;</button>
                    </div>
                </div>
                <div class="te-settings-body">
                    <nav class="te-settings-nav" id="te-settings-nav">
                        <button type="button" class="te-settings-nav-item active" data-panel="excluded-tables">테이블 추출 예외처리</button>
                        <button type="button" class="te-settings-nav-item" data-panel="excluded-refs">모듈 예외처리</button>
                    </nav>
                    <div class="te-settings-panel" id="te-settings-panel"></div>
                </div>
            </div>
        </div>
    `;

    var typeSel = container.querySelector('#te-id-type');
    var idInput = container.querySelector('#te-id-input');
    var keyinEl = container.querySelector('#te-keyin');
    var fromLinkInput = container.querySelector('#te-from-link');
    var toLinkInput = container.querySelector('#te-to-link');
    var generateBtn = container.querySelector('#te-generate');
    var modalEl = container.querySelector('#te-modal');
    var modalBodyEl = container.querySelector('#te-modal-body');
    var lastSql = '';   // '전체 복사'용 전체 SQL 캐시
    var PLACEHOLDER = {
        dbio: 'DBIO ID를 입력하세요 (여러 개는 쉼표로 구분해 입력하세요)',
        service: 'Service ID를 입력하세요 (여러 개는 쉼표로 구분해 입력하세요)',
        batch: 'Batch ID를 입력하세요 (여러 개는 쉼표로 구분해 입력하세요)',
        biz: 'Biz ID를 입력하세요 (여러 개는 쉼표로 구분해 입력하세요)',
    };

    typeSel.addEventListener('change', function () {
        idInput.placeholder = PLACEHOLDER[typeSel.value];
        updateProgVisibility();
    });

    // 업무그룹 콤보박스: 입력한 문자열로 목록을 필터링하는 검색형 드롭다운.
    // 백엔드 ResourceGroup(app/common/proframe/types.py)이 단일 소스 — 페이지 로드 시
    // /meta/resource-groups로 받아온다(둘 다 lazy 사용처라 도착 전에 쓰일 일 없음).
    var PROG_OPTIONS = [];
    fetch('meta/resource-groups')
        .then(function (res) { return res.json(); })
        .then(function (data) { PROG_OPTIONS = data.resource_groups; })
        .catch(function () { /* 실패해도 조용히 빈 목록 유지 — 콤보가 비어 보일 뿐 기능은 안 죽음 */ });
    // 추출 결과 접두사 필터 체크박스(테이블명 접두사)
    var PREFIXES = ['TRU', 'PFO', 'PTN', 'RPT'];
    var progInput = container.querySelector('#te-prog');
    var progList = container.querySelector('#te-prog-list');
    var progCombo = container.querySelector('#te-prog-combo');

    // DBIO는 리소스그룹(업무그룹)이 파일 경로에 쓰이지 않아 콤보박스를 숨긴다.
    // Service/Batch/Biz 등 그 외 타입에서만 리소스그룹을 선택받는다.
    function updateProgVisibility() {
        progCombo.style.display = typeSel.value === 'dbio' ? 'none' : '';
    }
    updateProgVisibility();   // 초기 상태(기본 DBIO) 반영

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

    // --- 추출하기: GET /table-extractor/{id_type}/{prog}/{id} 연결 ---
    var submitBtn = container.querySelector('#te-submit');
    var resultEl = container.querySelector('#te-result');

    // 좌(목록)/우(키 입력) 패널이 공유하는 상태 — 추출마다 초기화된다.
    var allMainTables = [];              // FEP 제외한 메인 목록(삭제 반영)
    var visibleTables = [];              // 현재 필터로 보이는(=이관 대상) 테이블. 필터 결과가 곧 대상.
    var pkMap = {};                      // {테이블: [PK컬럼]} — /pks 응답 캐시
    var pkLoaded = false;               // /pks 응답 도착 여부
    var keyinState = {};                 // {컬럼: {isDate, mode, value|single|from|to}} — 키 입력 값·모드 보존

    var ERROR_TITLE = {
        400: '요청 오류',
        404: '소스를 찾을 수 없음',
        501: '아직 지원하지 않는 유형',
        503: 'DB 연결 실패',
    };

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    // 입력창(#te-id-input)의 원본 텍스트 → ID 목록(쉼표 구분, 공백 제거, 중복 제거, 첫 등장 순서
    // 유지). 아직은 결과에서 첫 번째 ID만 실제로 조회하지만(여러 개 동시 조회는 다음 업데이트
    // 예정), 입력 파싱 자체는 미리 만들어둔다.
    var MAX_IDS = 50;

    function parseIds(raw) {
        var out = [];
        var seen = {};
        String(raw || '').split(/,+/).forEach(function (s) {
            var id = s.trim();
            if (!id || seen[id]) return;
            seen[id] = true;
            out.push(id);
        });
        return out;
    }

    function showEmpty(msg) {
        resultEl.innerHTML = '<div class="te-empty">' + escapeHtml(msg) + '</div>';
    }

    function resetKeyin() {
        allMainTables = [];
        visibleTables = [];
        pkMap = {};
        pkLoaded = false;
        keyinState = {};
        keyinEl.innerHTML = '<div class="te-keyin-box"><div class="te-empty">테이블을 추출하면 PK 입력란이 표시됩니다.</div></div>';
    }

    function showSpinner() {
        resetKeyin();  // 새 추출 시작 → 이전 키 입력 상태 정리
        resultEl.innerHTML = `
            <div class="te-empty">
                <div style="display:flex; flex-direction:column; align-items:center; gap:12px;">
                    <svg class="spinner" viewBox="0 0 50 50">
                        <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5" stroke-miterlimit="10"/>
                    </svg>
                    <span>원격 소스 조회 및 추출 중...</span>
                </div>
            </div>
        `;
    }

    function showError(title, detail) {
        resultEl.innerHTML = `
            <div class="error-box">
                <div class="error-header">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" width="16" height="16">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                    </svg>
                    <span>${escapeHtml(title)}</span>
                </div>
                <div style="font-size: 13px; line-height: 1.6;">${escapeHtml(detail)}</div>
            </div>
        `;
    }

    // --- 키 입력(PK 합집합) 컴포넌트: 선택된 테이블들의 PK 합집합을 실시간 표시 ---

    // 선택된 테이블들의 PK 컬럼 합집합(중복 제거, 첫 등장 순서 보존).
    // PK 정보가 없는(딕셔너리 미등록) 테이블은 합집합에 기여하지 않으며 별도로 경고한다.
    function computePkUnion(sel) {
        var out = [];
        var seen = {};
        sel.forEach(function (t) {
            (pkMap[t] || []).forEach(function (col) {
                if (!seen[col]) { seen[col] = true; out.push(col); }
            });
        });
        return out;
    }

    // 사내 관행: PK 컬럼명이 'date'로 끝나면 날짜 컬럼(단일/기간 선택 가능).
    function isDateColumn(col) {
        return /date$/i.test(col);
    }

    // 일반 PK 박스 내 우선 노출 순서(사내 관행상 자주 쓰는 키 먼저). 대소문자 무관 매칭.
    var PK_PRIORITY = ['mncm_code', 'fund_code', 'cmpn_code', 'itms_code'];
    function pkPriorityIndex(col) {
        var idx = PK_PRIORITY.indexOf(String(col).toLowerCase());
        return idx === -1 ? PK_PRIORITY.length : idx;
    }

    // PK_PRIORITY에 있는 컬럼을 그 순서대로 앞에 배치, 나머지는 원래 순서(첫 등장 순) 유지.
    // Array#sort는 안정 정렬이라 우선순위가 같은(모두 미등록인) 항목끼리는 순서가 보존된다.
    function sortByPkPriority(cols) {
        return cols.slice().sort(function (a, b) {
            return pkPriorityIndex(a) - pkPriorityIndex(b);
        });
    }

    // 컬럼별 키 입력 상태(모드/값)를 최초 1회 만들어 keyinState에 보존한다.
    // 필터·선택 변경으로 입력란이 다시 그려져도 여기서 복원 → 값과 단일/기간 모드가 유지됨.
    function ensureKeyinState(col) {
        if (!keyinState[col]) {
            keyinState[col] = isDateColumn(col)
                ? { isDate: true, mode: 'single', single: '', from: '', to: '' }
                : { isDate: false, value: '' };
        }
        return keyinState[col];
    }

    // 날짜 입력은 YYYYMMDD 8자리 숫자로 정제
    function sanitizeYmd(v) {
        return String(v).replace(/\D/g, '').slice(0, 8);
    }

    // YYYYMMDD 8자리이면서 실제 존재하는 날짜인지 검증(20250230·20251345 등 차단)
    function isValidYmd(v) {
        if (!/^\d{8}$/.test(v)) return false;
        var y = +v.slice(0, 4), m = +v.slice(4, 6), d = +v.slice(6, 8);
        var dt = new Date(y, m - 1, d);
        return dt.getFullYear() === y && dt.getMonth() === m - 1 && dt.getDate() === d;
    }

    function renderKeyin(errorMsg) {
        if (errorMsg) {
            keyinEl.innerHTML = '<div class="te-keyin-box"><div class="te-keyin-warn">' + escapeHtml(errorMsg) + '</div></div>';
            return;
        }

        var sel = visibleTables;   // 필터된(보이는) 결과가 곧 이관 대상
        if (!sel.length) {
            keyinEl.innerHTML = '<div class="te-keyin-box"><div class="te-empty">대상 테이블이 없습니다(필터를 확인하세요).</div></div>';
            return;
        }
        if (!pkLoaded) {
            keyinEl.innerHTML = '<div class="te-keyin-box"><div class="te-empty">PK 정보를 불러오는 중...</div></div>';
            return;
        }

        var missing = sel.filter(function (t) { return !pkMap[t] || !pkMap[t].length; });
        var union = computePkUnion(sel);

        if (!union.length) {
            keyinEl.innerHTML = '<div class="te-keyin-box"><div class="te-keyin-warn">대상 ' + sel.length + '개 테이블에 PK 정보가 없습니다.'
                + (missing.length ? ' (PK 정보 없음: ' + escapeHtml(missing.join(', ')) + ')' : '') + '</div></div>';
            return;
        }

        // 일반 PK와 날짜 PK를 각각 독립 스크롤 박스로 분리 표시. 일반 PK는 PK_PRIORITY 순서 우선.
        var normalCols = sortByPkPriority(union.filter(function (c) { return !isDateColumn(c); }));
        var dateCols = union.filter(isDateColumn);

        keyinEl.innerHTML =
            '<div class="te-keyin-head">PK 키 입력 <span class="count-badge">대상 ' + sel.length + '개 · PK ' + union.length + '개</span></div>'
            + '<div class="te-keyin-boxes">'
            + renderKeyinBox('일반 PK', normalCols, '키값 다 채울 필요 없음. 쉼표로 구분하여 복수건의 키값 입력시 in절로 작성됨')
            + renderKeyinBox('날짜 PK', dateCols)
            + '</div>'
            + (missing.length
                ? '<div class="te-keyin-note">PK 정보 없는 테이블: ' + escapeHtml(missing.join(', ')) + '</div>'
                : '');

        bindKeyinEvents();
    }

    // 일반/날짜 PK 박스 하나(제목 + 필드 그리드, 자체 스크롤) 렌더. 컬럼이 없으면 박스 자체를 생략.
    // note는 제목 오른쪽에 붙는 보조 안내문(일반 PK의 "여러 개는 쉼표로 구분" 힌트 등, 선택).
    function renderKeyinBox(title, cols, note) {
        if (!cols.length) return '';
        return '<div class="te-keyin-box">'
            + '<div class="te-keyin-section-title">' + escapeHtml(title) + ' <span class="count-badge">' + cols.length + '개</span>'
            + (note ? ' <span class="te-keyin-section-note">' + escapeHtml(note) + '</span>' : '')
            + '</div>'
            + '<div class="te-keyin-fields">'
            + cols.map(renderKeyinField).join('')
            + '</div>'
            + '</div>';
    }

    // 필드 하나 렌더: 일반=입력 1칸, 날짜=[단일|기간] 토글 + 모드별 입력
    function renderKeyinField(col) {
        var st = ensureKeyinState(col);
        var colHtml = '<span class="te-keyin-col" title="' + escapeHtml(col) + '">' + escapeHtml(col) + '</span>';

        if (!st.isDate) {
            return '<div class="te-keyin-field">'
                + colHtml
                + '<input type="text" class="te-keyin-input" data-role="value" data-pk="' + escapeHtml(col) + '"'
                + ' value="' + escapeHtml(st.value) + '" placeholder="' + escapeHtml(col) + ' 값">'
                + '</div>';
        }

        var toggle = '<span class="te-keyin-toggle" data-pk="' + escapeHtml(col) + '">'
            + '<button type="button" class="te-mode-btn' + (st.mode === 'single' ? ' active' : '') + '" data-mode="single">단일</button>'
            + '<button type="button" class="te-mode-btn' + (st.mode === 'range' ? ' active' : '') + '" data-mode="range">기간</button>'
            + '</span>';

        var inputs = st.mode === 'range'
            ? '<span class="te-keyin-range">'
                + '<input type="text" class="te-keyin-input" data-role="from" data-pk="' + escapeHtml(col) + '"'
                + ' inputmode="numeric" maxlength="8" value="' + escapeHtml(st.from) + '" placeholder="시작 YYYYMMDD">'
                + '<span class="te-range-sep">~</span>'
                + '<input type="text" class="te-keyin-input" data-role="to" data-pk="' + escapeHtml(col) + '"'
                + ' inputmode="numeric" maxlength="8" value="' + escapeHtml(st.to) + '" placeholder="종료 YYYYMMDD">'
                + '</span>'
            : '<input type="text" class="te-keyin-input" data-role="single" data-pk="' + escapeHtml(col) + '"'
                + ' inputmode="numeric" maxlength="8" value="' + escapeHtml(st.single) + '" placeholder="YYYYMMDD">';

        return '<div class="te-keyin-field te-keyin-field-date">'
            + '<span class="te-keyin-col-row">' + colHtml + toggle + '</span>'
            + inputs
            + '</div>';
    }

    // 입력/토글 이벤트를 keyinState에 라이브 반영(재렌더에도 값 유지). renderKeyin 뒤에 매번 호출.
    function bindKeyinEvents() {
        keyinEl.querySelectorAll('.te-keyin-input').forEach(function (inp) {
            inp.addEventListener('input', function (e) {
                var st = ensureKeyinState(e.currentTarget.getAttribute('data-pk'));
                var role = e.currentTarget.getAttribute('data-role');
                if (role === 'value') {
                    st.value = e.currentTarget.value;
                } else {
                    var v = sanitizeYmd(e.currentTarget.value);
                    e.currentTarget.value = v;     // 숫자 8자리 정제 반영
                    st[role] = v;                  // single | from | to
                }
            });
        });
        keyinEl.querySelectorAll('.te-mode-btn').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                var col = e.currentTarget.closest('.te-keyin-toggle').getAttribute('data-pk');
                ensureKeyinState(col).mode = e.currentTarget.getAttribute('data-mode');
                renderKeyin();   // 모드 전환 → 입력란 재구성
            });
        });
    }

    // --- 이관 SQL 생성 ---

    // keyinState → 서버 계약(컬럼별 조건)으로 변환. 단일/일반=eq, 기간=between.
    // (SQL 조립·값 이스케이프는 백엔드 POST /migrate-sql 에서 수행 — 테스트 가능하도록)
    function collectKeys() {
        var keys = {};
        Object.keys(keyinState).forEach(function (col) {
            var st = keyinState[col];
            if (st.isDate && st.mode === 'range') {
                keys[col] = { op: 'between', start: st.from, end: st.to };
            } else if (st.isDate) {
                keys[col] = { op: 'eq', value: st.single };
            } else {
                keys[col] = { op: 'eq', value: st.value };
            }
        });
        return keys;
    }

    async function generateSql() {
        if (!pkLoaded || !visibleTables.length) {
            App.showToast('먼저 테이블을 추출하세요.');
            return;
        }

        // 날짜(_date) 입력 검증: 값이 있으면 반드시 YYYYMMDD 8자리 유효 날짜(빈 값은 허용).
        // 현재 대상(필터된) 테이블의 PK 합집합에 속한 날짜 컬럼만 검사.
        var invalid = [];
        computePkUnion(visibleTables).forEach(function (col) {
            var st = keyinState[col];
            if (!st || !st.isDate) return;
            if (st.mode === 'range') {
                if (st.from && !isValidYmd(st.from)) invalid.push(col + ' 시작: "' + st.from + '"');
                if (st.to && !isValidYmd(st.to)) invalid.push(col + ' 종료: "' + st.to + '"');
            } else if (st.single && !isValidYmd(st.single)) {
                invalid.push(col + ': "' + st.single + '"');
            }
        });
        if (invalid.length) {
            alert('날짜 형식 오류 — YYYYMMDD(8자리) 유효 날짜여야 합니다:\n\n' + invalid.join('\n'));
            return;
        }

        try {
            var res = await fetch('table-extractor/migrate-sql', {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({
                    tables: visibleTables,
                    from_link: fromLinkInput.value.trim(),
                    to_link: toLinkInput.value.trim(),
                    keys: collectKeys(),
                }),
            });
            var data = await res.json();
            if (!res.ok) {
                var detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
                App.showToast('이관 SQL 생성 실패: ' + detail);
                return;
            }
            openModal(data);
        } catch (e) {
            App.showToast('이관 SQL 생성 요청 실패: ' + e.message);
        }
    }

    // --- 이관 SQL 팝업(모달): 그룹 박스 렌더 + 열기/닫기 ---

    // 응답을 접미사 그룹별 박스로 렌더한 뒤 모달을 연다.
    function openModal(data) {
        lastSql = data.sql || '';
        var groups = data.groups || [];
        // 이관 SQL이 만들어지지 않은 테이블 = PK 정보 없음 + 키가 하나도 안 맞음(전체삭제 방지)
        var notGenRows = [];
        (data.no_pk || []).forEach(function (t) { notGenRows.push({ name: t, reason: 'PK 정보 없음' }); });
        (data.skipped || []).forEach(function (t) { notGenRows.push({ name: t, reason: '입력 키와 PK 미매칭 ( 안전상의 이유로 전체 이관 방지 )' }); });

        var html = groups.length
            ? groups.map(function (g) {
                return '<div class="te-sql-group">'
                    + '<div class="te-sql-group-head">'
                    + '<span class="te-sql-group-key">' + escapeHtml(g.key) + '</span>'
                    + '<span class="count-badge">' + g.tables.length + '개</span>'
                    + '<button class="btn-secondary te-sql-copy">복사</button>'
                    + '</div>'
                    + '<textarea class="te-sql-box" readonly></textarea>'
                    + '</div>';
            }).join('')
            : '<div class="te-empty">생성된 이관 SQL이 없습니다(값 입력/대상 확인).</div>';

        if (notGenRows.length) {
            html += '<div class="te-sql-group te-nogen-group">'
                + '<div class="te-sql-group-head">'
                + '<span class="te-sql-group-key">이관 SQL 미생성 테이블</span>'
                + '<span class="count-badge">' + notGenRows.length + '개</span>'
                + '</div>'
                + '<table class="te-nogen-table"><thead><tr><th>테이블</th><th>사유</th></tr></thead><tbody>'
                + notGenRows.map(function (r) {
                    return '<tr><td>' + escapeHtml(r.name) + '</td><td>' + escapeHtml(r.reason) + '</td></tr>';
                }).join('')
                + '</tbody></table>'
                + '</div>';
        }

        modalBodyEl.innerHTML = html;

        // 그룹 박스: textarea value는 DOM API로 주입(HTML 이스케이프 회피) + 개별 복사
        var boxes = modalBodyEl.querySelectorAll('.te-sql-group:not(.te-nogen-group) .te-sql-box');
        groups.forEach(function (g, i) { if (boxes[i]) boxes[i].value = g.sql; });
        modalBodyEl.querySelectorAll('.te-sql-copy').forEach(function (btn, i) {
            btn.addEventListener('click', function () {
                App.copyToClipboard(groups[i].sql, groups[i].key + ' 그룹 SQL이 복사되었습니다.');
            });
        });

        modalEl.style.display = 'flex';
        if ((data.generated || []).length)
            App.showToast(data.generated.length + '개 테이블 이관 SQL 생성' + (notGenRows.length ? ' (미생성 ' + notGenRows.length + '개)' : ''));
        else
            App.showToast('생성된 이관 SQL이 없습니다.');
    }

    function closeModal() {
        modalEl.style.display = 'none';
    }

    // 이벤트 연결: 생성 버튼 + 모달 닫기/전체복사/배경클릭/Esc
    generateBtn.addEventListener('click', generateSql);
    container.querySelector('#te-modal-close').addEventListener('click', closeModal);
    container.querySelector('#te-modal-copy-all').addEventListener('click', function () {
        if (!lastSql) { App.showToast('복사할 SQL이 없습니다.'); return; }
        App.copyToClipboard(lastSql, '전체 이관 SQL이 복사되었습니다.');
    });
    // 배경 클릭 / Esc 로 닫기
    modalEl.addEventListener('mousedown', function (e) {
        if (e.target === modalEl) closeModal();
    });
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Escape') return;
        if (modalEl.style.display !== 'none') closeModal();
        if (settingsModalEl.style.display !== 'none') closeSettingsModal();
    });

    // --- 설정 팝업(사이드 네비 + 패널) ---
    // 각 탭(예외 테이블/모듈)은 "서버에서 목록 조회 → 로컬 draft로 편집 → 저장 버튼으로 POST"라는
    // 동일한 구조라 makeListSettingsPanel 팩토리 하나로 만든다. 새 탭을 추가하려면 네비 버튼 +
    // SETTINGS_PANELS에 팩토리 호출 한 줄만 더하면 된다.
    var settingsBtn = container.querySelector('#te-settings-btn');
    var settingsModalEl = container.querySelector('#te-settings-modal');
    var settingsNavEl = container.querySelector('#te-settings-nav');
    var settingsPanelEl = container.querySelector('#te-settings-panel');

    var EXCL_DELETE_ICON =
        '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">'
        + '<path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>'
        + '</svg>';

    // key/value 목록을 조회·편집·저장하는 설정 탭 하나를 만든다.
    // opts: { label, endpoint, requestKey, responseKey, placeholder, desc, normalize(raw)->string }
    // committed = 서버에 마지막으로 저장된 상태, draft = 팝업이 열려있는 동안의 작업 사본
    // (추가/삭제는 draft에만 반영, 저장 버튼을 눌러야 POST로 committed에 반영). 팝업을 열 때마다
    // 서버에서 다시 조회해 초기화하므로 저장 없이 닫은 편집은 버려진다.
    function makeListSettingsPanel(opts) {
        var committed = [];
        var draft = [];

        function isDirty() {
            if (draft.length !== committed.length) return true;
            var c = committed.slice().sort();
            var d = draft.slice().sort();
            return d.some(function (v, i) { return v !== c[i]; });
        }

        function addItem(raw) {
            var name = opts.normalize(raw);
            if (!name) return;
            if (draft.indexOf(name) !== -1) {
                App.showToast('"' + name + '"은(는) 이미 목록에 있습니다.');
                return;
            }
            draft.push(name);
            renderList();
        }

        function removeItem(name) {
            var idx = draft.indexOf(name);
            if (idx !== -1) draft.splice(idx, 1);
            renderList();
        }

        // 입력칸은 추가(Enter/버튼)뿐 아니라 이미 등록된(draft) 목록 실시간 필터로도 쓴다.
        function renderList() {
            var listEl = settingsPanelEl.querySelector('.te-excl-list');
            if (!listEl) return;

            var inputEl = settingsPanelEl.querySelector('.te-excl-input');
            var query = inputEl ? inputEl.value.trim().toUpperCase() : '';
            var visible = query
                ? draft.filter(function (v) { return v.toUpperCase().indexOf(query) !== -1; })
                : draft;

            if (!visible.length) {
                listEl.innerHTML = '<div class="te-empty" style="grid-column:1/-1;">'
                    + (draft.length ? '일치하는 항목이 없습니다.' : '등록된 항목이 없습니다.')
                    + '</div>';
            } else {
                listEl.innerHTML = visible.map(function (v) {
                    return '<div class="te-excl-item">'
                        + '<span class="te-excl-name" title="' + escapeHtml(v) + '">' + escapeHtml(v) + '</span>'
                        + '<button class="copy-btn te-del-btn" title="삭제" data-name="' + escapeHtml(v) + '">' + EXCL_DELETE_ICON + '</button>'
                        + '</div>';
                }).join('');
                listEl.querySelectorAll('.te-del-btn').forEach(function (btn) {
                    btn.addEventListener('click', function (e) {
                        removeItem(e.currentTarget.getAttribute('data-name'));
                    });
                });
            }

            // 미저장 변경사항 표시 + 저장 버튼 활성화 여부(필터와 무관하게 draft 전체 기준)
            var dirty = isDirty();
            var hintEl = settingsPanelEl.querySelector('.te-excl-dirty-hint');
            var saveBtn = settingsPanelEl.querySelector('.te-excl-save');
            if (hintEl) hintEl.textContent = dirty ? '저장되지 않은 변경사항이 있습니다' : '';
            if (saveBtn) saveBtn.disabled = !dirty;
        }

        // 저장 버튼: 작업 사본을 POST로 통째 저장(전체 교체) → 성공하면 서버 응답을 새 확정 상태로 반영.
        async function save() {
            var saveBtn = settingsPanelEl.querySelector('.te-excl-save');
            if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = '저장 중...'; }
            try {
                var body = {};
                body[opts.requestKey] = draft;
                var res = await fetch(opts.endpoint, {
                    method: 'POST',
                    headers: { 'content-type': 'application/json' },
                    body: JSON.stringify(body),
                });
                var data = await res.json();
                if (!res.ok) {
                    var detail = typeof data.detail === 'string' ? data.detail : '저장 실패';
                    App.showToast(opts.label + ' 저장 실패: ' + detail);
                    return;
                }
                committed = data[opts.responseKey] || [];
                draft = committed.slice();
                App.showToast(opts.label + ' ' + committed.length + '개가 저장되었습니다.');
            } catch (e) {
                App.showToast(opts.label + ' 저장 요청 실패: ' + e.message);
            } finally {
                if (saveBtn) saveBtn.textContent = '저장';
                renderList();   // 성공/실패 무관하게 최신 draft·dirty 상태로 리스트/버튼 재계산
            }
        }

        function renderBody() {
            settingsPanelEl.innerHTML = `
                <div class="te-excl-desc">${opts.desc}</div>
                <div class="te-excl-add-row">
                    <input type="text" class="te-excl-input" placeholder="${escapeHtml(opts.placeholder)}" autocomplete="off">
                    <button class="btn-secondary te-excl-add">추가</button>
                </div>
                <div class="te-excl-list"></div>
                <div class="te-excl-save-row">
                    <span class="te-excl-dirty-hint"></span>
                    <button class="btn-secondary te-excl-save">저장</button>
                </div>
            `;
            renderList();

            var input = settingsPanelEl.querySelector('.te-excl-input');
            function tryAdd() {
                addItem(input.value);
                input.value = '';
                input.focus();
                renderList();   // 입력칸을 비웠으니 필터도 초기화된 전체 목록으로 다시 그린다
            }
            settingsPanelEl.querySelector('.te-excl-add').addEventListener('click', tryAdd);
            input.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') tryAdd();
            });
            input.addEventListener('input', renderList);   // 타이핑할 때마다 등록된 목록을 실시간 필터링
            settingsPanelEl.querySelector('.te-excl-save').addEventListener('click', save);
        }

        // 팝업 진입점: 로딩 표시 후 서버에서 최신 목록을 조회해 본문을 그린다.
        return async function renderPanel() {
            settingsPanelEl.innerHTML = '<div class="te-empty">' + opts.label + ' 목록을 불러오는 중...</div>';
            try {
                var res = await fetch(opts.endpoint);
                var data = await res.json();
                if (!res.ok) {
                    var detail = typeof data.detail === 'string' ? data.detail : '조회 실패';
                    settingsPanelEl.innerHTML = '<div class="te-keyin-warn">' + opts.label + ' 목록을 불러오지 못했습니다: ' + escapeHtml(detail) + '</div>';
                    return;
                }
                committed = data[opts.responseKey] || [];
            } catch (e) {
                settingsPanelEl.innerHTML = '<div class="te-keyin-warn">' + opts.label + ' 목록 요청 실패: ' + escapeHtml(e.message) + '</div>';
                return;
            }
            draft = committed.slice();
            renderBody();
        };
    }

    var SETTINGS_PANELS = {
        'excluded-tables': makeListSettingsPanel({
            label: '예외 테이블',
            endpoint: 'table-extractor/excluded-tables',
            requestKey: 'tables',
            responseKey: 'tables',
            placeholder: '테이블명 입력 후 Enter',
            desc: '여기에 등록한 테이블은 추출 결과 목록에서 항상 제외됩니다.<br>추가/삭제 후 <b>저장</b>을 눌러야 반영됩니다.',
            normalize: function (raw) { return String(raw || '').trim().toUpperCase(); },
        }),
        'excluded-refs': makeListSettingsPanel({
            label: '모듈 예외처리',
            endpoint: 'table-extractor/excluded-refs',
            requestKey: 'ids',
            responseKey: 'ids',
            placeholder: 'DBIO/모듈 ID 입력 후 Enter',
            desc: '여기에 등록한 DBIO/모듈 ID는 재귀 탐색 중 참조로 만나면 소스를 들여다보지 않고 건너뜁니다.'
                + '<br>최상위로 직접 조회 요청한 ID에는 적용되지 않습니다.<br>추가/삭제 후 <b>저장</b>을 눌러야 반영됩니다.',
            normalize: function (raw) { return String(raw || '').trim(); },   // ID는 대소문자 구분 매칭이라 그대로 보존
        }),
    };

    function openSettingsPanel(key) {
        settingsNavEl.querySelectorAll('.te-settings-nav-item').forEach(function (btn) {
            btn.classList.toggle('active', btn.getAttribute('data-panel') === key);
        });
        (SETTINGS_PANELS[key] || function () {})();
    }

    function openSettingsModal() {
        var activeBtn = settingsNavEl.querySelector('.te-settings-nav-item.active') || settingsNavEl.querySelector('.te-settings-nav-item');
        openSettingsPanel(activeBtn ? activeBtn.getAttribute('data-panel') : 'excluded-tables');
        settingsModalEl.style.display = 'flex';
    }

    function closeSettingsModal() {
        settingsModalEl.style.display = 'none';
    }

    settingsBtn.addEventListener('click', openSettingsModal);
    settingsNavEl.querySelectorAll('.te-settings-nav-item').forEach(function (btn) {
        btn.addEventListener('click', function () {
            openSettingsPanel(btn.getAttribute('data-panel'));
        });
    });
    container.querySelector('#te-settings-close').addEventListener('click', closeSettingsModal);
    settingsModalEl.addEventListener('mousedown', function (e) {
        if (e.target === settingsModalEl) closeSettingsModal();
    });

    // 추출된 전체 테이블의 PK를 1회 조회해 캐시(필터 변경 시엔 서버 재호출 없이 합집합만 재계산)
    async function fetchPks(tables) {
        try {
            var res = await fetch('table-extractor/pks', {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({ tables: tables }),
            });
            var data = await res.json();
            if (!res.ok) {
                pkMap = {};
                pkLoaded = true;
                var detail = typeof data.detail === 'string' ? data.detail : 'PK 조회 실패';
                renderKeyin('PK 조회 실패: ' + detail);
                return;
            }
            pkMap = data.pks || {};
            pkLoaded = true;
            renderKeyin();
        } catch (e) {
            pkMap = {};
            pkLoaded = true;
            renderKeyin('PK 조회 요청 실패: ' + e.message);
        }
    }

    // 경유한 DBIO/service/biz 모듈 ID 한 그룹(추출경로 섹션의 하위 블록 하나) — 비어 있으면 렌더 안 함.
    // 그룹 제목이 곧 토글 버튼 — 기본은 접힌 상태, 클릭하면 목록이 나타난다.
    function renderTraceGroup(label, ids) {
        if (!ids || !ids.length) return '';
        return `
            <div class="te-trace-group">
                <button type="button" class="te-trace-toggle" aria-expanded="false">
                    <span class="te-trace-chevron">▶</span>
                    <span class="te-trace-group-title">${label}</span>
                    <span class="count-badge">${ids.length}개</span>
                </button>
                <div class="te-trace-list te-trace-list-collapsed">
                    ${ids.map(function (id) {
                        return '<div class="te-trace-item" title="' + escapeHtml(id) + '">' + escapeHtml(id) + '</div>';
                    }).join('')}
                </div>
            </div>
        `;
    }

    // 배치 추출에서 일부 ID가 실패했을 때(사유 포함) 보여주는 표 — 이관 SQL 모달의
    // "이관 SQL 미생성 테이블" 표(.te-nogen-table)와 동일한 {ID,사유} 2열 구조를 재사용한다.
    function renderFailedSection(failed) {
        return `
            <div class="te-failed-section">
                <div class="te-failed-title">일부 항목 조회 실패 <span class="count-badge">${failed.length}개</span></div>
                <table class="te-nogen-table"><thead><tr><th>ID</th><th>사유</th></tr></thead><tbody>
                    ${failed.map(function (f) {
                        return '<tr><td>' + escapeHtml(f.file_id) + '</td><td>' + escapeHtml(f.error) + '</td></tr>';
                    }).join('')}
                </tbody></table>
            </div>
        `;
    }

    function showAllFailed(failed) {
        resetKeyin();
        resultEl.innerHTML = '<div class="te-empty">추출된 테이블이 없습니다.</div>' + renderFailedSection(failed);
    }

    function renderTables(tables, batches, dbios, services, bizs, failed) {
        // FEP 접두사 테이블은 메인 목록에서 빼고 아래 별도 섹션에 읽기 전용으로 표시
        var fepTables = tables.filter(function (t) { return t.indexOf('FEP') === 0; });
        allMainTables = tables.filter(function (t) { return t.indexOf('FEP') !== 0; });

        var fepSection = fepTables.length ? `
            <div class="te-fep-section">
                <div class="te-fep-title">FEP 테이블 <span class="count-badge">${fepTables.length}개</span> <span class="te-fep-note">fep 이관 미지원</span></div>
                <div class="te-fep-list">
                    ${fepTables.map(function (t) {
                        return '<div class="te-fep-item" title="' + escapeHtml(t) + '">' + escapeHtml(t) + '</div>';
                    }).join('')}
                </div>
            </div>
        ` : '';

        // 발견된 batch 참조 — 재귀 중 참조만 되고 소스는 안 들여다본 배치 ID. 발견됐을 때만 칸이 생긴다.
        batches = batches || [];
        var batchSection = batches.length ? `
            <div class="te-batch-section">
                <div class="te-batch-title">발견된 batch <span class="count-badge">${batches.length}개</span> <span class="te-batch-note">참조된 배치는 직접 조회 요청. 자동 참조 기능 지원안함</span></div>
                <div class="te-batch-list">
                    ${batches.map(function (b) {
                        return '<div class="te-batch-item" title="' + escapeHtml(b) + '">' + escapeHtml(b) + '</div>';
                    }).join('')}
                </div>
            </div>
        ` : '';

        // 배치 추출 중 일부 ID가 실패했으면(부분성공) 사유와 함께 별도로 안내한다.
        failed = failed || [];
        var failedSection = failed.length ? renderFailedSection(failed) : '';

        // 추출경로: 경유한 DBIO/service/biz 모듈 ID — 셋 다 비어 있으면 섹션 자체를 생략한다.
        // 그룹별로 접혀 있다가 토글을 누르면 목록이 나타난다.
        var traceBody = renderTraceGroup('DBIO', dbios) + renderTraceGroup('Service', services) + renderTraceGroup('Biz', bizs);
        var traceSection = traceBody ? `
            <div class="te-trace-section">
                <div class="te-trace-title">추출경로 <span class="te-trace-note">추출 과정에서 경유한 모듈</span></div>
                ${traceBody}
            </div>
        ` : '';

        resultEl.innerHTML = `
            <div class="te-prefix-filters">
                ${PREFIXES.map(function (p) {
                    return '<label><input type="checkbox" class="te-prefix" value="' + p + '"> ' + p + '</label>';
                }).join('')}
                <input type="text" id="te-filter" class="te-filter-input" placeholder="테이블 필터..." autocomplete="off">
            </div>
            <div class="te-result-header">
                <div class="result-title">
                    <span>추출 결과</span>
                    <span class="count-badge" id="te-count">${allMainTables.length}개</span>
                </div>
                <div class="te-result-actions">
                    <button class="btn-secondary" id="te-copy-all">전체 복사</button>
                </div>
            </div>
            <div class="te-table-list" id="te-table-list"></div>
            ${fepSection}
            ${batchSection}
            ${failedSection}
            ${traceSection}
        `;

        var listEl = resultEl.querySelector('#te-table-list');
        var countEl = resultEl.querySelector('#te-count');
        var filterEl = resultEl.querySelector('#te-filter');

        // 현재 UI 상태(텍스트 필터 + 접두사 체크박스)를 읽어 매칭 계산 (FEP 제외한 메인 목록 대상)
        //   텍스트: 부분일치(AND) / 접두사: 체크된 것 중 하나로 시작(OR), 아무것도 안 체크하면 제약 없음
        function computeMatches() {
            var q = filterEl.value.trim().toUpperCase();
            var checked = Array.prototype.slice.call(resultEl.querySelectorAll('.te-prefix:checked'))
                               .map(function (c) { return c.value; });
            return allMainTables.filter(function (t) {
                if (q && t.indexOf(q) === -1) return false;
                if (checked.length && !checked.some(function (p) { return t.indexOf(p) === 0; })) return false;
                return true;
            });
        }

        function renderList() {
            var matches = computeMatches();
            visibleTables = matches;   // 필터된 결과 = 이관 대상. 우측 PK 입력란이 이 목록을 따른다.
            countEl.textContent = matches.length + '개';

            if (!matches.length) {
                listEl.innerHTML = '<div class="te-empty" style="grid-column:1/-1;">일치하는 테이블이 없습니다.</div>';
                renderKeyin();
                return;
            }
            listEl.innerHTML = matches.map(function (t) {
                return `
                    <div class="te-table-item">
                        <span class="te-table-name" title="${escapeHtml(t)}">${escapeHtml(t)}</span>
                        <span class="te-item-actions">
                            <button class="copy-btn" title="복사" data-table="${escapeHtml(t)}">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke-width="2"></rect>
                                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-width="2"></path>
                                </svg>
                            </button>
                            <button class="copy-btn te-del-btn" title="삭제" data-table="${escapeHtml(t)}">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
                                </svg>
                            </button>
                        </span>
                    </div>
                `;
            }).join('');
            renderKeyin();   // 목록 갱신될 때마다 우측 PK 합집합도 재계산
            listEl.querySelectorAll('.copy-btn:not(.te-del-btn)').forEach(function (btn) {
                btn.addEventListener('click', function (e) {
                    var name = e.currentTarget.getAttribute('data-table');
                    App.copyToClipboard(name, '"' + name + '" 테이블명이 복사되었습니다.');
                });
            });
            listEl.querySelectorAll('.te-del-btn').forEach(function (btn) {
                btn.addEventListener('click', function (e) {
                    var name = e.currentTarget.getAttribute('data-table');
                    var idx = allMainTables.indexOf(name);
                    if (idx !== -1) allMainTables.splice(idx, 1);   // 메인 목록에서 제거 → 목록/개수/PK 입력란 모두 renderList가 갱신
                    renderList();
                    App.showToast('"' + name + '" 삭제됨');
                });
            });
        }

        filterEl.addEventListener('input', renderList);
        resultEl.querySelectorAll('.te-prefix').forEach(function (cb) {
            cb.addEventListener('change', renderList);
        });

        resultEl.querySelector('#te-copy-all').addEventListener('click', function () {
            if (!visibleTables.length) {
                App.showToast('복사할 테이블이 없습니다.');
                return;
            }
            App.copyToClipboard(visibleTables.join(', '), visibleTables.length + '개 테이블명이 쉼표로 구분되어 복사되었습니다.');
        });

        // 추출경로: 그룹 제목을 누르면 목록이 펼쳐지고/접힌다 (기본은 접힌 상태).
        resultEl.querySelectorAll('.te-trace-toggle').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var list = btn.parentElement.querySelector('.te-trace-list');
                var expanded = btn.getAttribute('aria-expanded') === 'true';
                btn.setAttribute('aria-expanded', String(!expanded));
                btn.querySelector('.te-trace-chevron').textContent = expanded ? '▶' : '▼';
                list.classList.toggle('te-trace-list-collapsed');
            });
        });

        renderList();                // 목록 렌더 + visibleTables 세팅 + renderKeyin(로딩 상태)
        fetchPks(allMainTables);     // 추출 직후 전체 테이블 PK 1회 조회 → 캐시 후 renderKeyin
    }

    submitBtn.addEventListener('click', async function () {
        var idType = typeSel.value;
        var ids = parseIds(idInput.value);

        // 쉼표 대신 공백으로 여러 ID를 구분하면 comma split에서 안 나뉘어 공백 포함 문자열
        // 하나가 ID 1개로 잘못 인식된다("A , B"처럼 쉼표 앞뒤 공백은 parseIds의 trim이 이미
        // 처리해서 여기 안 걸림) — 서버까지 보내면 이상한 404로 나타나므로 화면에서 먼저 막는다.
        if (ids.some(function (id) { return /\s/.test(id); })) {
            showError('입력값 오류', 'ID는 쉼표(,)로만 구분해주세요. 공백으로 구분된 값이 있습니다.');
            return;
        }

        // 클라이언트 선검증: 서버의 422(장황한 pydantic 오류) 대신 친절한 메시지
        // DBIO는 리소스그룹을 받지 않음 → 2세그먼트 경로(생략). 그 외 타입만 리소스그룹을 검증해 3세그먼트로.
        var prog = null;
        if (idType !== 'dbio') {
            prog = progInput.value.trim().toUpperCase();
            if (PROG_OPTIONS.indexOf(prog) === -1) {
                showError('입력값 오류', '업무그룹을 목록에서 선택하세요.');
                return;
            }
        }
        if (!ids.length) {
            showError('입력값 오류', 'ID를 입력하세요.');
            return;
        }
        if (ids.length > MAX_IDS) {
            showError('입력값 오류', 'ID는 최대 ' + MAX_IDS + '개까지 입력할 수 있습니다.');
            return;
        }

        showSpinner();

        try {
            var res = await fetch('table-extractor/' + encodeURIComponent(idType) + '/extract-batch', {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({ resource_group: prog || null, file_ids: ids }),
            });
            var data = await res.json();

            if (!res.ok) {
                var detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
                showError(ERROR_TITLE[res.status] || '서버 오류', detail);
                return;
            }

            // 우측 '이관 sql' 박스(textarea)는 다음 단계에서 구현 — 지금은 채우지 않는다.
            // 테이블이 0개여도 batch 참조가 있으면(예: 배치 소스만 있고 내부 DBIO 픽스처가
            // 아직 없는 경우) 그 목록은 보여줘야 하므로, 둘 다 비었을 때만 완전 empty 처리한다.
            var tables = data.tables || [];
            var batches = data.batches || [];
            var dbios = data.dbios || [];
            var services = data.services || [];
            var bizs = data.bizs || [];
            var failed = data.failed || [];
            if (tables.length === 0 && batches.length === 0) {
                if (failed.length) {
                    showAllFailed(failed);
                } else {
                    showEmpty('추출된 테이블이 없습니다.');
                }
                return;
            }
            renderTables(tables, batches, dbios, services, bizs, failed);

        } catch (e) {
            showError('서버 요청 실패', e.message);
        }
    });
}());
