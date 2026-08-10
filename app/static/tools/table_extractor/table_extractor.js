(function () {
    var container = document.getElementById('page-table-extractor');
    if (!container) return;

    container.innerHTML = `
        <div class="header">
            <div class="badge">테이블 추출 및 이관 도구</div>
            <h1>Table Extractor</h1>
            <p>서비스 ID 또는 DBIO ID를 입력하면 참조하는 모든 테이블을 추출합니다.</p>
            <p>현재 프로시저, 함수 내부의 테이블은 추출 기능은 지원하지 않습니다. </p>
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
            <input type="text" id="te-id-input" placeholder="DBIO ID를 입력하세요">
            <button id="te-submit">추출하기</button>
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
        dbio: 'DBIO ID를 입력하세요',
        service: 'Service ID를 입력하세요',
        batch: 'Batch ID를 입력하세요',
        biz: 'Biz ID를 입력하세요',
    };

    typeSel.addEventListener('change', function () {
        idInput.placeholder = PLACEHOLDER[typeSel.value];
        updateProgVisibility();
    });

    // 업무그룹 콤보박스: 입력한 문자열로 목록을 필터링하는 검색형 드롭다운
    var PROG_OPTIONS = ['PCSP', 'PCSH', 'NCOM', 'NCSP', 'PCOM', 'PPFR', 'RLGR'];
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

    function showEmpty(msg) {
        resultEl.innerHTML = '<div class="te-empty">' + escapeHtml(msg) + '</div>';
    }

    function resetKeyin() {
        allMainTables = [];
        visibleTables = [];
        pkMap = {};
        pkLoaded = false;
        keyinState = {};
        keyinEl.innerHTML = '<div class="te-empty">테이블을 추출하면 PK 입력란이 표시됩니다.</div>';
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
            keyinEl.innerHTML = '<div class="te-keyin-warn">' + escapeHtml(errorMsg) + '</div>';
            return;
        }

        var sel = visibleTables;   // 필터된(보이는) 결과가 곧 이관 대상
        if (!sel.length) {
            keyinEl.innerHTML = '<div class="te-empty">대상 테이블이 없습니다(필터를 확인하세요).</div>';
            return;
        }
        if (!pkLoaded) {
            keyinEl.innerHTML = '<div class="te-empty">PK 정보를 불러오는 중...</div>';
            return;
        }

        var missing = sel.filter(function (t) { return !pkMap[t] || !pkMap[t].length; });
        var union = computePkUnion(sel);

        if (!union.length) {
            keyinEl.innerHTML = '<div class="te-keyin-warn">대상 ' + sel.length + '개 테이블에 PK 정보가 없습니다.'
                + (missing.length ? ' (PK 정보 없음: ' + escapeHtml(missing.join(', ')) + ')' : '') + '</div>';
            return;
        }

        keyinEl.innerHTML =
            '<div class="te-keyin-head">PK 키 입력 <span class="count-badge">대상 ' + sel.length + '개 · PK ' + union.length + '개</span></div>'
            + '<div class="te-keyin-fields">'
            + union.map(renderKeyinField).join('')
            + '</div>'
            + (missing.length
                ? '<div class="te-keyin-note">PK 정보 없는 테이블: ' + escapeHtml(missing.join(', ')) + '</div>'
                : '');

        bindKeyinEvents();
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
            var res = await fetch('/table-extractor/migrate-sql', {
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
        if (e.key === 'Escape' && modalEl.style.display !== 'none') closeModal();
    });

    // 추출된 전체 테이블의 PK를 1회 조회해 캐시(필터 변경 시엔 서버 재호출 없이 합집합만 재계산)
    async function fetchPks(tables) {
        try {
            var res = await fetch('/table-extractor/pks', {
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

    function renderTables(tables) {
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

        renderList();                // 목록 렌더 + visibleTables 세팅 + renderKeyin(로딩 상태)
        fetchPks(allMainTables);     // 추출 직후 전체 테이블 PK 1회 조회 → 캐시 후 renderKeyin
    }

    submitBtn.addEventListener('click', async function () {
        var idType = typeSel.value;
        var id = idInput.value.trim();

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
        if (!id) {
            showError('입력값 오류', 'ID를 입력하세요.');
            return;
        }

        showSpinner();

        try {
            var url = '/table-extractor/' + encodeURIComponent(idType) + '/' +
                (prog ? encodeURIComponent(prog) + '/' : '') +
                encodeURIComponent(id);
            var res = await fetch(url);
            var data = await res.json();

            if (!res.ok) {
                var detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
                showError(ERROR_TITLE[res.status] || '서버 오류', detail);
                return;
            }

            // 우측 '이관 sql' 박스(textarea)는 다음 단계에서 구현 — 지금은 채우지 않는다.
            if (!data.tables || data.tables.length === 0) {
                showEmpty('추출된 테이블이 없습니다.');
                return;
            }
            renderTables(data.tables);

        } catch (e) {
            showError('서버 요청 실패', e.message);
        }
    });
}());
