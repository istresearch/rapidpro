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
    const btnSubmit = document.querySelector("#btn-send-command");
    const dropdownMenu = document.querySelector('#command-select');
    const commandConfirmDialog = document.querySelector('#command-confirmation');

    btnSubmit.addEventListener("click", function (e) {
        e.preventDefault();
        const selectedCommand = dropdownMenu.value;
        const commandType = dropdownMenu.options[dropdownMenu.selectedIndex].dataset.type;
        const needsConfirmation = dropdownMenu.options[dropdownMenu.selectedIndex].dataset.confirm === 'true';

        let argsValue = [];
        if (commandType === 'bool' || commandType === 'apps' || commandType === 'select') {
            argsValue.push(document.getElementById("options-select").value);
        } else if (commandType === 'text') {
            argsValue.push(document.getElementById("text-input").value);
        }

        let selectedUUIDs = getCheckedData('object-uuid');
        let deviceIDs = [];
        selectedUUIDs.forEach(uuid => {
            const rowDeviceID = $('tbody').find(`tr[data-object-uuid='${uuid}']`).find('td:nth-child(3)').text().trim();
            deviceIDs.push(rowDeviceID);
        });

        if (needsConfirmation) {
            commandConfirmDialog.classList.remove("hide");
            commandConfirmDialog.open = true;
            commandConfirmDialog.addEventListener("temba-button-clicked", function(e) {
                if (!e.detail.button.secondary) {
                    showSpinner();
                    commandConfirmDialog.classList.add("hide");
                    commandConfirmDialog.open = false;
                    sendCommand(argsValue, deviceIDs, selectedCommand);
                }
                commandConfirmDialog.open = false;
            });
            
        } else {
            showSpinner();
            sendCommand(argsValue, deviceIDs, selectedCommand);
        }
    });
}

function sendCommand(argsValue, deviceIDs, selectedCommand) {
    const requestData = {
        device_ids: deviceIDs,
        commands: [{
            command: selectedCommand,
            args: argsValue
        }]
    };

    makeHttpRequest({
        url: `/pm/`,
        data: JSON.stringify(requestData),
        success: (resp) => {
            putToastInToaster('alert-success', resp.msg);
        },
        error: (resp) => {
            let errorMessage = 'Error sending command';
            try {
                const errorData = JSON.parse(resp.responseText);
                errorMessage = `${errorData.error.cause}: ${errorData.error.message}`;
            } catch (e) {
                console.error('Error parsing JSON response:', resp.responseText);
            }
            putToastInToaster('alert-warning', errorMessage);
        }
    }).always(() => {
        hideSpinner();
    });
}

function populateDropdown() {
    if (window.contextData.commands_list.command_groups) {
        const commandGroups = window.contextData.commands_list.command_groups;
        const dropdown = document.getElementById("command-select");
        dropdown.innerHTML = ''; // Clear existing options if any

        commandGroups.forEach(group => {
            const optgroup = document.createElement("optgroup");
            optgroup.label = group.name;

            group.commands.forEach(command => {
                if (!command.hidden) {
                    const option = document.createElement("option");
                    option.value = command.command;
                    option.textContent = command.label;
                    option.dataset.type = command.type;
                    option.dataset.confirm = command.confirm;
                    option.dataset.description = command.description;
                    if (command.options) {
                        option.dataset.options = JSON.stringify(command.options);
                    }
                    optgroup.appendChild(option);
                }
            });

            dropdown.appendChild(optgroup);
        });

        dropdown.addEventListener('change', (e) => {
            const selectedCommand = commandGroups.flatMap(group => group.commands).find(command => command.command === e.target.value);

            const optionsContainer = document.getElementById("options-container");
            const textContainer = document.getElementById("text-container");
            const optionsSelect = document.getElementById("options-select");
            const textInput = document.getElementById("text-input");
            const descriptionContainer = document.getElementById("command-description");

            if (selectedCommand) {
                descriptionContainer.innerText = selectedCommand.description || '';

                if (['bool', 'apps', 'select'].includes(selectedCommand.type)) {
                    optionsContainer.style.display = 'block';
                    textContainer.style.display = 'none';
                    optionsSelect.innerHTML = ''; // Clear previous options

                    if (selectedCommand.type === 'bool') {
                        ['true', 'false'].forEach(value => {
                            const option = document.createElement("option");
                            option.value = value;
                            option.textContent = value.charAt(0).toUpperCase() + value.slice(1);
                            optionsSelect.appendChild(option);
                        });
                    } else if (selectedCommand.options) {
                        Object.entries(selectedCommand.options).forEach(([key, value]) => {
                            const opt = document.createElement("option");
                            opt.value = key;
                            opt.textContent = value;
                            optionsSelect.appendChild(opt);
                        });
                    }
                } else if (selectedCommand.type === 'text') {
                    textContainer.style.display = 'block';
                    optionsContainer.style.display = 'none';
                    textInput.value = ''; // Clear previous input
                } else {
                    optionsContainer.style.display = 'none';
                    textContainer.style.display = 'none';
                }
            }
        });

        dropdown.dispatchEvent(new Event('change'));
    }
}

window.addEventListener('DOMContentLoaded', function (e) {
    wireupActionPurge();
    wireupActionRename();
    wireupActionCommand();
});
