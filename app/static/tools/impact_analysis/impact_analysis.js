(function () {
    var container = document.getElementById('page-impact-analysis');
    if (!container) return;

    container.innerHTML = `
        <div class="header">
            <div class="badge">영향도 분석</div>
            <h1>Impact Analysis</h1>
            <p>테이블명 또는 비즈모듈명을 입력하면, 테이블은 그 테이블을 참조하는 DBIO를, 비즈모듈은 곧바로 그 모듈을 찾습니다.<br>DBIO·비즈모듈을 펼치면 연결된 비즈·서비스·배치 모듈을 조회하고, 비즈모듈은 다시 펼쳐 그 비즈를 부르는 상위 모듈을 계속 따라갈 수 있습니다(서비스·배치는 항상 최상위).</p>
        </div>

        <form class="ia-search-bar" id="ia-search-form">
            <select id="ia-target-type" class="ia-search-select">
                <option value="table">Table</option>
                <option value="biz">Biz</option>
            </select>
            <input type="text" id="ia-search-input" placeholder="테이블명을 입력하세요 (예: PFO_FUND_BS)" autocomplete="off">
            <div class="ia-group-filter" id="ia-group-filter">
                <button type="button" class="ia-group-filter-btn" id="ia-group-filter-btn">업무그룹 전체</button>
                <div class="ia-group-filter-panel" id="ia-group-filter-panel"></div>
            </div>
            <button type="submit" class="ia-search-btn" id="ia-search-btn">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <circle cx="11" cy="11" r="6.5"/>
                    <path stroke-linecap="round" d="M20 20l-4.3-4.3"/>
                </svg>
                <span>검색</span>
            </button>
        </form>

        <div class="ia-workspace">
            <div class="card ia-panel">
                <div class="ia-panel-title">검색 결과</div>
                <div class="ia-results" id="ia-results"></div>
            </div>
            <div class="card ia-panel">
                <div class="ia-panel-title">
                    <span>집계</span>
                    <button type="button" class="copy-btn" id="ia-summary-copy-btn" title="집계 결과 전체 복사">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke-width="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-width="2"></path>
                        </svg>
                    </button>
                </div>
                <div class="ia-summary" id="ia-summary"></div>
            </div>
        </div>
    `;

    var form = container.querySelector('#ia-search-form');
    var typeSel = container.querySelector('#ia-target-type');
    var searchInput = container.querySelector('#ia-search-input');
    var resultsEl = container.querySelector('#ia-results');
    var summaryEl = container.querySelector('#ia-summary');
    var summaryCopyBtn = container.querySelector('#ia-summary-copy-btn');
    var groupFilter = container.querySelector('#ia-group-filter');
    var groupFilterBtn = container.querySelector('#ia-group-filter-btn');
    var groupFilterPanel = container.querySelector('#ia-group-filter-panel');
    var PLACEHOLDER = {
        table: '테이블명을 입력하세요 (예: PFO_FUND_BS)',
        biz: '비즈모듈명을 입력하세요 (예: MZPFM_FundInfoSave)',
    };
    // 백엔드 ResourceGroup(app/common/proframe/types.py)이 단일 소스 — 페이지 로드 시
    // /meta/resource-groups로 받아온다(table_extractor.js와 동일한 패턴).
    var PROG_OPTIONS = [];

    // 업무그룹 필터: 선택 안 함(빈 Set) = 전체 대상. 다음 라운드의 DBIO→호출모듈 조회가
    // getSelectedGroups()를 그대로 쿼리 파라미터로 넘겨 grep 범위를 좁히는 데 쓴다.
    var selectedGroups = new Set();

    function updateGroupFilterLabel() {
        groupFilterBtn.textContent = selectedGroups.size
            ? selectedGroups.size + '개 선택'
            : '업무그룹 선택';
    }

    function updateToggleAllLabel() {
        toggleAllBtn.textContent = selectedGroups.size === PROG_OPTIONS.length
            ? '전체해제'
            : '전체선택';
    }

    var toggleAllBtn = document.createElement('button');
    toggleAllBtn.type = 'button';
    toggleAllBtn.className = 'ia-group-filter-toggle-all';
    toggleAllBtn.addEventListener('click', function () {
        if (selectedGroups.size === PROG_OPTIONS.length) {
            selectedGroups.clear();
        } else {
            PROG_OPTIONS.forEach(function (group) {
                selectedGroups.add(group);
            });
        }
        renderGroupFilterPanel();
        updateGroupFilterLabel();
    });

    function renderGroupFilterPanel() {
        groupFilterPanel.innerHTML = '';
        updateToggleAllLabel();
        groupFilterPanel.appendChild(toggleAllBtn);

        PROG_OPTIONS.forEach(function (group) {
            var label = document.createElement('label');
            label.className = 'ia-group-filter-item';

            var text = document.createElement('span');
            text.className = 'ia-group-filter-item-text';
            text.textContent = group;

            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = group;
            checkbox.checked = selectedGroups.has(group);
            checkbox.addEventListener('change', function () {
                if (checkbox.checked) {
                    selectedGroups.add(group);
                } else {
                    selectedGroups.delete(group);
                }
                updateGroupFilterLabel();
                updateToggleAllLabel();
            });

            label.appendChild(text);
            label.appendChild(checkbox);
            groupFilterPanel.appendChild(label);
        });
    }

    function getSelectedGroups() {
        return Array.from(selectedGroups);
    }

    // PROG_OPTIONS가 도착하기 전엔 패널이 비어 보이므로, fetch가 끝난 뒤에 처음 렌더한다.
    fetch('meta/resource-groups')
        .then(function (res) { return res.json(); })
        .then(function (data) {
            PROG_OPTIONS = data.resource_groups;
            renderGroupFilterPanel();
            updateGroupFilterLabel();
        })
        .catch(function () { /* 실패해도 조용히 빈 목록 유지 — 필터가 비어 보일 뿐 검색 자체는 안 죽음 */ });

    groupFilterBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        groupFilterPanel.classList.toggle('open');
    });

    document.addEventListener('click', function (e) {
        if (!groupFilter.contains(e.target)) {
            groupFilterPanel.classList.remove('open');
        }
    });

    typeSel.addEventListener('change', function () {
        searchInput.placeholder = PLACEHOLDER[typeSel.value];
    });

    function renderMessage(text) {
        resultsEl.innerHTML = '';
        var p = document.createElement('p');
        p.className = 'ia-empty';
        p.textContent = text;
        resultsEl.appendChild(p);
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text == null ? '' : String(text);
        return div.innerHTML;
    }

    // 우측 집계 패널 상태 — 지금까지 "펼쳐본" 결과만 실시간으로 누적(A안: 전체를 강제로
    // 다 펼치는 완전 집계가 아니라, 사용자가 실제로 조회한 것만 중복 제거해 쌓는 방식).
    // 새 검색을 시작하면 초기화한다.
    var agg = {
        dbios: new Set(),
        services: new Set(),
        bizs: new Set(),
        batches: new Set(),
    };

    function resetAggregate() {
        agg.dbios.clear();
        agg.services.clear();
        agg.bizs.clear();
        agg.batches.clear();
        renderSummary();
    }

    function renderSummaryGroup(label, set) {
        var ids = Array.from(set).sort();
        if (!ids.length) {
            return '<div class="ia-summary-group ia-summary-group-empty">' + escapeHtml(label) + ' 없음</div>';
        }
        return `
            <div class="ia-summary-group">
                <div class="ia-summary-group-title">${escapeHtml(label)} <span class="count-badge">${ids.length}개</span></div>
                <ul class="ia-summary-items">
                    ${ids.map(function (id) { return '<li>' + escapeHtml(id) + '</li>'; }).join('')}
                </ul>
            </div>
        `;
    }

    function renderSummary() {
        summaryEl.innerHTML =
            renderSummaryGroup('DBIO', agg.dbios) +
            renderSummaryGroup('Service', agg.services) +
            renderSummaryGroup('Biz', agg.bizs) +
            renderSummaryGroup('Batch', agg.batches);
    }

    renderSummary();

    // 집계 전체를 클립보드에 복사 — 그룹별로 한 줄, id는 쉼표로 구분(빈 그룹은 "없음").
    summaryCopyBtn.addEventListener('click', function () {
        if (!agg.dbios.size && !agg.services.size && !agg.bizs.size && !agg.batches.size) {
            App.showToast('복사할 집계 결과가 없습니다.');
            return;
        }
        var lines = [
            ['DBIO', agg.dbios],
            ['Service', agg.services],
            ['Biz', agg.bizs],
            ['Batch', agg.batches],
        ].map(function (entry) {
            var ids = Array.from(entry[1]).sort();
            return '[' + entry[0] + '] ' + (ids.length ? ids.join(', ') : '없음');
        });
        App.copyToClipboard(lines.join('\n'), '집계 결과가 클립보드에 복사되었습니다.');
    });

    // 현재 펼쳐가고 있는 조상 체인(루트→현재 직전까지의 {refType, refId} 목록). Biz는
    // 서로를 순환 참조할 수 있어(A가 B를 부르고 B가 다시 A를 부르는 등), 그 체인에 이미
    // 있는 id를 다시 후보로 보여주면 사용자가 끝없이 펼치는 루프에 빠질 수 있다 — 그래서
    // 결과에서 조상과 같은 id는 아예 숨긴다.
    function isAncestor(ancestors, refType, refId) {
        return ancestors.some(function (a) {
            return a.refType === refType && a.refId === refId;
        });
    }

    // DBIO 펼침 바디 안의 한 그룹(Service/Batch, 확장 불가) — 비어 있으면 "없음" 문구만 표시.
    function renderCallerGroup(label, ids) {
        if (!ids || !ids.length) {
            return '<div class="ia-caller-group ia-caller-group-empty">' + escapeHtml(label) + ' 없음</div>';
        }
        return `
            <div class="ia-caller-group">
                <div class="ia-caller-group-title">${escapeHtml(label)} <span class="count-badge">${ids.length}개</span></div>
                <ul class="ia-caller-items">
                    ${ids.map(function (id) { return '<li>' + escapeHtml(id) + '</li>'; }).join('')}
                </ul>
            </div>
        `;
    }

    // 하나의 펼침 가능 항목(DBIO 최상위 또는 재귀 중인 Biz)을 만들고 토글을 바로 연결한다.
    function makeExpandableItem(refType, refId, ancestors) {
        var li = document.createElement('li');
        li.className = 'ia-dbio-item';
        li.innerHTML = `
            <button type="button" class="ia-dbio-toggle" aria-expanded="false">
                <span class="ia-dbio-chevron">▶</span>
                <span class="ia-dbio-id">${escapeHtml(refId)}</span>
            </button>
            <div class="ia-dbio-body ia-dbio-body-collapsed"></div>
        `;
        var btn = li.querySelector('.ia-dbio-toggle');
        var body = li.querySelector('.ia-dbio-body');

        btn.addEventListener('click', function () {
            var wasExpanded = btn.getAttribute('aria-expanded') === 'true';
            btn.setAttribute('aria-expanded', String(!wasExpanded));
            btn.querySelector('.ia-dbio-chevron').textContent = wasExpanded ? '▶' : '▼';
            body.classList.toggle('ia-dbio-body-collapsed', wasExpanded);

            if (!wasExpanded && !body.dataset.loaded) {
                loadCallers(refType, refId, body, ancestors.concat([{ refType: refType, refId: refId }]));
            }
        });

        return li;
    }

    // Biz 그룹은 확장 가능 — 조상 체인에 이미 있는 id는 순환 방지를 위해 목록에서 뺀다.
    function renderBizGroup(ids, ancestors) {
        var visible = (ids || []).filter(function (id) {
            return !isAncestor(ancestors, 'biz', id);
        });

        var wrap = document.createElement('div');
        wrap.className = 'ia-caller-group';

        if (!visible.length) {
            wrap.classList.add('ia-caller-group-empty');
            wrap.textContent = 'Biz 없음';
            return wrap;
        }

        var title = document.createElement('div');
        title.className = 'ia-caller-group-title';
        title.textContent = 'Biz ';
        var badge = document.createElement('span');
        badge.className = 'count-badge';
        badge.textContent = visible.length + '개';
        title.appendChild(badge);
        wrap.appendChild(title);

        var ul = document.createElement('ul');
        ul.className = 'ia-dbio-list';
        visible.forEach(function (id) {
            ul.appendChild(makeExpandableItem('biz', id, ancestors));
        });
        wrap.appendChild(ul);

        return wrap;
    }

    // DBIO(또는 Biz) 하나를 펼쳤을 때 그 바디에 호출 모듈(service/biz/batch)을 채운다.
    // 업무그룹 필터가 선택돼 있으면 grep 범위를 좁히도록 그대로 쿼리 파라미터로 넘긴다.
    // refType은 "dbio" 또는 "biz" — 백엔드 라우트가 /callers/{ref_type}/{ref_id} 형태.
    // ancestors는 여기까지 펼쳐온 조상 체인(순환 참조 방지용, Biz 재귀 펼치기에서 씀).
    function loadCallers(refType, refId, body, ancestors) {
        body.innerHTML = '<p class="ia-empty">조회 중...</p>';
        var qs = getSelectedGroups()
            .map(function (g) { return 'resource_groups=' + encodeURIComponent(g); })
            .join('&');
        var url = 'impact-analysis/callers/' + refType + '/' + encodeURIComponent(refId) + (qs ? '?' + qs : '');

        fetch(url)
            .then(function (res) {
                return res.json().then(function (data) {
                    if (!res.ok) throw new Error(data.detail || '조회에 실패했습니다.');
                    return data;
                });
            })
            .then(function (data) {
                body.dataset.loaded = 'true';
                body.innerHTML = renderCallerGroup('Service', data.services);
                body.appendChild(renderBizGroup(data.bizs, ancestors));
                body.insertAdjacentHTML('beforeend', renderCallerGroup('Batch', data.batches));

                data.services.forEach(function (id) { agg.services.add(id); });
                data.bizs.forEach(function (id) { agg.bizs.add(id); });
                data.batches.forEach(function (id) { agg.batches.add(id); });
                renderSummary();
            })
            .catch(function (err) {
                delete body.dataset.loaded;
                body.innerHTML = '<p class="ia-empty">' + escapeHtml(err.message || '조회에 실패했습니다.') + '</p>';
            });
    }

    function renderDbios(dbios) {
        resultsEl.innerHTML = '';
        if (!dbios.length) {
            renderMessage('참조하는 DBIO를 찾지 못했습니다.');
            return;
        }
        var ul = document.createElement('ul');
        ul.className = 'ia-dbio-list';
        dbios.forEach(function (id) {
            ul.appendChild(makeExpandableItem('dbio', id, []));
            agg.dbios.add(id);
        });
        resultsEl.appendChild(ul);
        renderSummary();
    }

    // 비즈모듈 검색: 입력한 ID 자체가 이미 루트라 DBIO처럼 1차 조회가 따로 없다 —
    // 바로 펼칠 수 있는 단일 항목으로 보여주고, 펼치면 loadCallers("biz", id, ...)가 호출된다.
    function renderBizRoot(id) {
        resultsEl.innerHTML = '';
        var ul = document.createElement('ul');
        ul.className = 'ia-dbio-list';
        ul.appendChild(makeExpandableItem('biz', id, []));
        resultsEl.appendChild(ul);
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        var query = searchInput.value.trim();
        if (!query) return;

        resetAggregate();

        if (typeSel.value === 'biz') {
            renderBizRoot(query);
            return;
        }

        renderMessage('검색 중...');

        fetch('impact-analysis/dbios/' + encodeURIComponent(query))
            .then(function (res) {
                return res.json().then(function (data) {
                    if (!res.ok) throw new Error(data.detail || '조회에 실패했습니다.');
                    return data;
                });
            })
            .then(function (data) {
                renderDbios(data.dbios);
            })
            .catch(function (err) {
                renderMessage(err.message || '조회에 실패했습니다.');
            });
    });
}());
