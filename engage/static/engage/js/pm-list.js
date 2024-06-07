let elListButtons;
function handleRowSelection(checkbox) {
    const row = checkbox.closest("tr");
    if (row) {
        if (checkbox.checked) {
            row.classList.add('checked');
            elListButtons.classList.add('visible');
        } else {
            row.classList.remove('checked');
            // if nothing else is also checked, hide bulk action buttons
            if ( !document.querySelector('tr.checked') ) {
                elListButtons.classList.remove('visible');
            }
        }
    }
}

function handleRowClicked(event) {
    if (event.target.tagName !== "TEMBA-CHECKBOX") {
      const row = event.target.closest('tr');
      const uuid = row.getAttribute("data-object-uuid");
      gotoLink("/pm/read/" + uuid + "/");
    }
}

function handleSortOnHeader(e) {
    let searchParams = new URLSearchParams(window.location.search);
    const params = new Proxy(searchParams, {
        get: (searchParams, prop) => searchParams.get(prop),
    });
    let sortOn = params._order;
    let bSortDirAsc = !sortOn.startsWith('-');
    let theSortField = (bSortDirAsc) ? sortOn : sortOn.slice(1);
    let theNewSortField = e.target.id.substr(e.target.id.indexOf("-")+1);

    if ( theNewSortField === theSortField ) {
        theNewSortField = (bSortDirAsc ? '-' : '') + theNewSortField;
    }
    searchParams.set('sort_on', theNewSortField);
    window.location.search = searchParams.toString();
}

$(document).ready(function(){
    elListButtons = document.querySelector('.list-buttons-container');
    $("th.header").click(handleSortOnHeader);
    populateDropdown();
});

function getCheckedData(data2get='object-uuid') {
    let checkedUuids = [];
    const checks = $('.object-row.checked');
    for (let i = 0; i < checks.length; i++) {
        checkedUuids.push($(checks[i]).data(data2get));
    }
    return checkedUuids;
}

function makeHttpRequest(params) {
    const request = {
        url: params.url,
        type: params.data ? 'POST' : 'GET',
        data: params.data,
        headers: params.headers,
        success: params.success,
        error: params.error
    };

    return $.ajax(request);
}

function wireupActionPurge() {
    const menuitemPurge = document.querySelector("#action-purge");
    const dlgPurge = document.querySelector("#purge-confirmation");
    if ( menuitemPurge && dlgPurge ) {
        menuitemPurge.addEventListener("click", function(e) {
            dlgPurge.classList.remove("hide");
            dlgPurge.open = true;
        });

        dlgPurge.addEventListener("temba-button-clicked", function(e) {
            if (!e.detail.button.secondary) {
                showSpinner();
                let objList = getCheckedData('object-id');
                Promise.all(objList.map((id) => {
                    return makeHttpRequest({
                        url: `/channels/purge/pm_service/${id}`,
                        success: (resp) => {
                            putToastInToaster('alert-success', resp);
                        },
                    });
                })).then(
                    () => {
                        hideSpinner();
                    },
                    () => {
                        hideSpinner();
                    }
                );
            }
            dlgPurge.open = false;
        });
    }
}

function wireupActionRename() {
    const menuitem = document.querySelector("#action-rename");
    const btnSubmit = document.querySelector("#btn-submit-rename");
    if ( menuitem && btnSubmit ) {
        btnSubmit.addEventListener("click", function(e) {
            showSpinner();
            const inputNameFormat = document.querySelector('#pm-name-format');
            let theNameFormat = inputNameFormat.value;
            if ( !theNameFormat ) {
                theNameFormat = '';
            }
            let objList = getCheckedData('object-id');
            Promise.all(objList.map((id) => {
                return makeHttpRequest({
                    url: `/pm/rename_channels/${id}/`,
                    data: {name_format: theNameFormat},
                }).then((resp) => {
                    putToastInToaster('alert-success', resp.msg);
                    const rowDeviceName = $('tbody').find(`tr[data-object-id='${resp.id}'] > td > a`);
                    if ( rowDeviceName ) {
                        rowDeviceName.text(resp.name);
                    }
                }, (resp) => {
                    putToastInToaster('alert-warning', resp.msg);
                });
            })).then(
                () => {
                    hideSpinner();
                },
                () => {
                    hideSpinner();
                }
            );
        });
    }
}

function wireupActionCommand() {
    const menuitem = document.querySelector("#action-command");
    const btnSubmit = document.querySelector("#btn-send-command");
    const dropdownMenu = document.querySelector('#command-select');
    const optionsSelect = document.getElementById("options-select");
    const textInput = document.getElementById("text-input");

    if (menuitem && btnSubmit) {
        btnSubmit.addEventListener("click", function (e) {
            showSpinner();

            const selectedCommand = dropdownMenu.value;
            const commandType = dropdownMenu.options[dropdownMenu.selectedIndex].dataset.type;
            let argsValue = null;

            // Determine the Args value based on the type of command
            if (commandType === 'bool' || commandType === 'apps' || commandType === 'select') {
                argsValue = optionsSelect.value;
            } else if (commandType === 'text') {
                argsValue = textInput.value;
            }

            let selectedUUIDs = getCheckedData('object-uuid');
            let deviceIDs = [];
            selectedUUIDs.forEach((uuid) => {
                const rowDeviceID = $('tbody').find(`tr[data-object-uuid='${uuid}']`).find('td:nth-child(3)').text().trim();
                if (rowDeviceID) {
                    deviceIDs.push(rowDeviceID);
                }
            });

            let requestData = {
                UserID: window.contextData.UserID,
                OrgID: window.contextData.OrgID,
                Commands: [selectedCommand],
                DeviceIDs: deviceIDs
            };

            if (argsValue !== null) {
                requestData.Args = argsValue;
            }

            makeHttpRequest({
                url: `/postoffice/engage/commands/send`,
                headers: {
                    'po-api-key': window.contextData.po_api_key
                },
                data: requestData,
            }).then((resp) => {
                putToastInToaster('alert-warning', resp.msg);
            }).always(() => {
                hideSpinner();
            });
        });
    }
}

function populateDropdown() {
    makeHttpRequest({
        url: '/postoffice/engage/commands/list',
        headers: {
            'po-api-key': window.contextData.po_api_key
        },
        success: (response) => {
            const commands = response.data.commands;
            const dropdown = document.getElementById("command-select");
            dropdown.innerHTML = ''; // Clear existing options if any
            // const optionsContainer = document.getElementById("options-container");
            // const textContainer = document.getElementById("text-container");
            // const optionsSelect = document.getElementById("options-select");
            // const textInput = document.getElementById("text-input");

            Object.entries(commands).forEach(([key, command]) => {
                const option = document.createElement("option");
                option.value = key;
                option.textContent = command.label;
                option.dataset.type = command.type;
                if (command.options) {
                    option.dataset.options = JSON.stringify(command.options);
                }
                dropdown.appendChild(option);
            });

            dropdown.addEventListener('change', (e) => {
                const selectedOption = commands[e.target.value];
                const optionsContainer = document.getElementById("options-container");
                const textContainer = document.getElementById("text-container");
                const optionsSelect = document.getElementById("options-select");
                const textInput = document.getElementById("text-input");
            
                // Clear previous options
                optionsSelect.innerHTML = '';
                textInput.value = '';
            
                if (['bool', 'apps', 'select'].includes(selectedOption.type)) {
                    optionsContainer.style.display = 'block';
                    textContainer.style.display = 'none';
            
                    if (selectedOption.type === 'bool') {
                        // Special handling for boolean type
                        const trueOption = document.createElement("option");
                        trueOption.value = 'true';
                        trueOption.textContent = 'True';
                        optionsSelect.appendChild(trueOption);
            
                        const falseOption = document.createElement("option");
                        falseOption.value = 'false';
                        falseOption.textContent = 'False';
                        optionsSelect.appendChild(falseOption);
                    } else if (selectedOption.options) {
                        // Normal handling for 'apps' and 'select' with predefined options
                        Object.entries(selectedOption.options).forEach(([key, value]) => {
                            const opt = document.createElement("option");
                            opt.value = key;
                            opt.textContent = value;
                            optionsSelect.appendChild(opt);
                        });
                    }
                } else if (selectedOption.type === 'text') {
                    textContainer.style.display = 'block';
                    optionsContainer.style.display = 'none';
                } else {
                    optionsContainer.style.display = 'none';
                    textContainer.style.display = 'none';
                }
            });
            
        },
        error: (error) => {
            console.log('Error fetching commands:', error);
        }
    });
}


window.addEventListener('DOMContentLoaded', function (e) {
    wireupActionPurge();
    wireupActionRename();
    wireupActionCommand();
});
