var bridge = null;

new QWebChannel(qt.webChannelTransport, function(channel){

    bridge = channel.objects.bridge;

});
console.log("Leaflet version:", L.version);

var map = L.map("map");

map.setView([20.5937, 78.9629], 5);

var tiles = L.tileLayer(
    "https://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
    {
        maxZoom:19
    }
);

tiles.on("loading",function(){
    console.log("Loading tiles...");
});

tiles.on("load",function(){
    console.log("Tiles loaded.");
});

tiles.on("tileerror",function(e){
    console.log("Tile Error URL:", e.tile.src);

fetch(e.tile.src)
.then(r=>{
    console.log(
        "Status:",
        r.status,
        r.statusText
    );
})
.catch(err=>{
    console.log(
        "Fetch Error:",
        err
    );
});
});

tiles.addTo(map);
var marker = null;

map.on("click", function(e){

    if(marker){
        map.removeLayer(marker);
    }

    marker = L.marker(e.latlng).addTo(map);

    console.log(
        "Clicked:",
        e.latlng.lat,
        e.latlng.lng
    );

    if(bridge){
        bridge.updateCoordinates(
            e.latlng.lat,
            e.latlng.lng
        );
    }

});



function moveToLocation(lat, lng){

    map.setView([lat, lng], 13);

    if(marker){
        map.removeLayer(marker);
    }

    marker = L.marker([lat, lng]).addTo(map);
}  
   
