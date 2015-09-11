var map, response;
var layers = {
    mapTiles: true,
    buildings: false,
    generatedPolygons: false,
    computedPolygon: true,
    truthPolygon: true
};
var kmlBlob, kmlLink = document.createElement('a');

function initialize() {
    $('a').click(function() {
        $(this).blur();
    });

    L.Icon.Default.imagePath = 'lib/leaflet';
    window.map = L.map('map');
    updateMap();

    $('#info').click(function(event) {
        $(this).toggleClass('expanded');
        updateInfo();
    });
    updateInfo();

    bindKeyboardShortcuts();
}

function updateInfo() {
    var info = $('#info');
    if (window.response) {
        switch (window.response.type) {
        case 'location':
            var location = window.response.data;
            if ($('#info').hasClass('expanded')) {
                var image = location.image_file_path ? '<img width="300" src="' + location.image_file_path + '"/>' : 'Not available';

                var truthWay = 'TODO';
                var computedWay = 'TODO';
                var surs = '';
                for (key in location.surs) {
                    surs += key + ' &rarr; ' + location.surs[key] + '<br>';
                }

                var kmlLinkText = window.kmlLink ? 'Download' : 'Not available';
                html = '<table><tr><td colspan="2" class="summary">Location</td></tr>';
                html += '<tr><td class="label">Name</td><td>' + location.name + '</td></tr>';
                html += '<tr><td class="label">Coordinates</td><td>' + location.point.join(', ') + '</td></tr>';
                html += '<tr><td class="label">SURs</td><td>' + surs + '</td></tr>';
                html += '<tr><td class="label">KML</td><td><a href="javascript:downloadKML();">' + kmlLinkText + '</a></td></tr>';
                html += '<tr><td class="label">Image</td><td>' + image + '</td></tr>';
                html += '</table>';
            } else {
                html = 'Location <strong>' + location.name + '</strong> @ ' + location.point.join(', ') + '<div class="dlimage"><a href="javascript:downloadKML()"><img src="core/info-download-kml.png"/></a></div>';
            }
            break;
        }
    } else {
        html = 'No information available.';
    }

    info.html(html);
    $('a').click(function(event) {
        event.stopPropagation();
    });
}

function downloadKML() {
    var ua = window.navigator.userAgent;
    if (ua.indexOf('MSIE') > 0 || ua.match(/Trident.*rv\:11\./)) {
        // Internet Explorer
        navigator.saveBlob = navigator.saveBlob || navigator.msSaveBlob || navigator.mozSaveBlob || navigator.webkitSaveBlob;
        if (!navigator.saveBlob) {
            alert('This feature cannot be used with this browser.');
            return;
        }
        navigator.saveBlob(window.kmlBlob, window.response.data.kml_name);
    } else {
        // Not Internet Explorer
        document.body.appendChild(window.kmlLink);
        window.kmlLink.click();
        document.body.removeChild(window.kmlLink);
    }
}

function updateKMLLink() {
    if (window.Blob) {
        window.kmlBlob = new Blob([window.response.data.kml], {type: 'application/vnd.google-earth.kml'});
        window.kmlLink.href = window.URL.createObjectURL(window.kmlBlob);
        window.kmlLink.download = window.response.data.kml_name;
    }
}

function addWay(name, way, options, clickable) {
    // TODO Other polygon types ("streets")
    var polygon = L.polygon(way.polygon, options).addTo(map);

    if (clickable) {
        polygon.on('click', function(event) {
            var way = this.way;
            var content = '<table><tr><td class="summary" colspan="2">' + name + '</td></tr>';
            for (key in way.tags) {
                content += '<tr><td>' + key + '</td><td>' + way.tags[key] + '</td></tr>';
            }
            content += '</table>';
            L.popup({'closeButton': false, 'maxWidth': 400}).setLatLng(event.latlng).setContent(content).openOn(map);
        });
        polygon.way = way;
    }

    return polygon;
}

function updateMap() {
    window.map.remove();
    window.map = L.map('map');
    window.map.attributionControl.addAttribution('Maps: <a href="http://www.openstreetmap.org" title="Open Street Map">&copy; OpenStreetMap contributors</a> (<a href="http://www.openstreetmap.org/copyright" title="License">License</a>)');
    if (window.response) {
        switch (window.response.type) {
        case 'location':
            // Add OSM map tiles
            var location = window.response.data;
            window.map.setView(location.point, 17);
            if (window.layers.mapTiles) {
                L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {}).addTo(window.map);
            }
            L.marker(location.point).addTo(window.map);

            // Add correct ("truth") way
            if (window.layers.truthPolygon && location.truth) {
                addWay('Truth polygon', location.truth, {color: '#0f0', weight: 5});
            }

            // Add computed way
            if (window.layers.computedPolygon) {
                addWay('Computed polygon', location.computed, {color: '#f00', weight: 5});
            }

            // Visualize polygons (ways) near the location
            for (name in location.ways) {
                var way = location.ways[name];
                var tags = way.tags;
                var show = false;
                show |= window.layers.buildings && tags['building'] !== undefined;
                show |= window.layers.generatedPolygons && tags['source'] == 'gen_from_osm_node';
                if (show) {
                    addWay(name, way, {color: '#000', weight: 1}, true);
                }
            }

            break;
        }
    } else {
        // Hamburg Department of Informatics!
        if (window.layers.mapTiles) {
            window.map.setView([53.598192, 9.932419], 16);
        }
        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {}).addTo(window.map);
    }
}

function queryLocation() {
    var options = {
        'input': {
            title: 'Query location',
            html: 'Name: <select name="location_name" disabled="disabled" style="width:338px"></select>',
            buttons: { Query: 0, Cancel: 1 },
            focus: 'select',
            submit: function(event, value, message, formValues) {
                event.preventDefault();
                if (value == 1) {
                    $.prompt.close();
                    return;
                }

                $.prompt.goToState('working');

                formValues.action = 'query_location';
                $.post('', formValues, function(response) {
                    if (response.result === 'success') {
                        $.prompt.close();
                        window.response = response;
                        updateKMLLink();
                        updateMap();
                        updateInfo();
                    } else {
                        $.prompt.getStateContent('failure').children('.jqimessage').html('Failed to query location.<br/>Reason: ' + response.reason);
                        $.prompt.goToState('failure');
                    }
                });
            }
        },
        'failure': {
            title: 'Query location',
            buttons: { OK: 0, Retry: 1 },
            submit: function(event, value, message, formValues) {
                event.preventDefault();
                if (value == 1) {
                    $.prompt.goToState('input');
                    return;
                }

                $.prompt.close();
            }
        },
        'working': {
            title: 'Query location',
            html: 'Querying location...',
            buttons: { }
        }
    };

    var prompt = $.prompt(options);
    prompt.on('impromptu:loaded', function(event) {
        $.post('', {'action': 'query_location_names'}, function(response) {
            var select = $.prompt.getStateContent('input').find('select');
            if (response.result == 'success') {
                options = '';
                for (key in response.data) {
                    location_name = response.data[key];
                    options += '<option>' + location_name + '</option>';
                }
            }
            select.attr('disabled', false);
            select.html(options);

            if (window.response && window.response.type == 'location') {
                select.find('option:contains("' + window.response.data.name + '")').prop('selected', true);
            }
        });
    });
}

function setLayers() {
    var l = window.layers;
    var options = {
        'input': {
            title: 'Set layers',
            html: '<table>'
                + '<tr><td>Map tiles:</td><td><input type="checkbox" name="mapTiles"' + (l.mapTiles ? ' checked' : '') + '/></select></td></tr>'
                + '<tr><td>Buildings:</td><td><input type="checkbox" name="buildings"' + (l.buildings ? ' checked' : '') + '/></select></td></tr>'
                + '<tr><td>Generated polygons:</td><td><input type="checkbox" name="generatedPolygons"' + (l.generatedPolygons ? ' checked' : '') + '/></select></td></tr>'
                + '<tr><td>Computed polygon:</td><td><input type="checkbox" name="computedPolygon"' + (l.computedPolygon ? ' checked' : '') + '/></select></td></tr>'
                + '<tr><td>Truth polygon:</td><td><input type="checkbox" name="truthPolygon"' + (l.truthPolygon ? ' checked' : '') + '/></select></td></tr>'
                + '</table>',
            buttons: { 'Set layers': 0, Cancel: 1 },
            focus: 'select',
            submit: function(event, value, message, formValues) {
                event.preventDefault();
                if (value == 1) {
                    $.prompt.close();
                    return;
                }

                window.layers = {
                    'mapTiles': formValues.mapTiles !== undefined,
                    'buildings': formValues.buildings !== undefined,
                    'generatedPolygons': formValues.generatedPolygons !== undefined,
                    'computedPolygon': formValues.computedPolygon !== undefined,
                    'truthPolygon': formValues.truthPolygon !== undefined
                };
                $.prompt.close();
                updateMap();
            }
        },
    };

    $.prompt(options);
}

function processLocation() {
    var imageBase64;

    var options = {
        'input': {
            title: 'Process location',
            html: '<table>'
                + '<tr><td>Latitude:</td><td><input style="width:108px" name="lat" value=""></td><td width="20"></td><td>Longitude:</td><td><input style="width:108px" name="lon" value=""></td></tr>'
                + '<tr><td>Radius:</td><td colspan="4"><input style="width:314px" name="radius" value="200"></input></td></tr>'
                + '<tr><td>SURs:</td><td colspan="4"><textarea style="width:314px" name="surs"></textarea></td></tr>'
                + '<tr><td>Image:</td><td colspan="4"><input style="width:318px" name="image" type="file" maxlength="10485760" accept="image/*"></td></tr>'
                + '</table>',
            buttons: { Process: 0, Cancel: 1 },
            focus: 'input[name="lat"]',
            submit: function(event, value, message, formValues) {
                event.preventDefault();
                if (value == 1) {
                    $.prompt.close();
                    return;
                }

                $.prompt.goToState('working');

                formValues.action = 'process_location';
                formValues.image_base_64 = imageBase64;

                $.post('', formValues, function(response) {
                    if (response.result === 'success') {
                        $.prompt.close();
                        window.response = response;
                        updateKMLLink();
                        updateMap();
                        updateInfo();
                    } else {
                        $.prompt.getStateContent('failure').children('.jqimessage').html('Failed to process location.<br/>Reason: ' + response.reason);
                        $.prompt.goToState('failure');
                    }
                });
            }
        },
        'failure': {
            title: 'Process location',
            buttons: { OK: 0, Retry: 1 },
            submit: function(event, value, message, formValues) {
                event.preventDefault();
                if (value == 1) {
                    $.prompt.goToState('input');
                    return;
                }

                $.prompt.close();
            }
        },
        'working': {
            title: 'Process location',
            html: 'Processing location...',
            buttons: { }
        }
    };

    var prompt = $.prompt(options);
    prompt.on('impromptu:loaded', function(event) {
        var form = $.prompt.getStateContent('form');
        var fileReader, file;
        if (!window.File || !window.FileReader || !window.FileList || !window.Blob) {
            console.log('This browser does not support the FileReader API.');
            form.find('input:file').prop('disabled', true);
        }

        // form.find('input[name="image"]').change(function() {
        $('input[name="image"]').change(function() {
            file = $(this).prop('files')[0];
            fileReader.readAsDataURL(file);
        });

        function fileContentsRead() {
            imageBase64 = fileReader.result;
        }

        fileReader = new FileReader();
        fileReader.onload = fileContentsRead;
    });
}

function bindKeyboardShortcuts() {
    $(document).bind('keydown', 'return', function() {
        if ($('.jqibox').length == 0) {
            queryLocation();
        }
    });
}

$(function() {
    initialize();
});