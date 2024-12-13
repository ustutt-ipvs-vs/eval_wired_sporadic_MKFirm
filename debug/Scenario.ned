
import inet.networks.base.TsnNetworkBase;
import inet.node.contract.IEthernetNetworkNode;
import inet.node.ethernet.EthernetLink;
import inet.node.tsn.TsnDevice;
import inet.node.tsn.TsnSwitch;

network EmergencyNetwork extends TsnNetworkBase
{
    submodules:

        n0: TsnSwitch {
            @display("p=545.7649920754856,554.8219299541895");
            numEthInterfaces = 3;
            hasOutgoingStreams = true;
            bridging.directionReverser.delayer.typename = "PacketDelayer";
            bridging.directionReverser.delayer.delay = 2000ns;
            eth[*].macLayer.queue.numTrafficClasses = 8;
            eth[0].bitrate = 100Mbps;
            eth[1].bitrate = 100Mbps;
            eth[2].bitrate = 100Mbps;
        }

        n1: TsnSwitch {
            @display("p=615.9301168405145,719.4620954632776");
            numEthInterfaces = 4;
            hasOutgoingStreams = true;
            bridging.directionReverser.delayer.typename = "PacketDelayer";
            bridging.directionReverser.delayer.delay = 2000ns;
            eth[*].macLayer.queue.numTrafficClasses = 8;
            eth[0].bitrate = 100Mbps;
            eth[1].bitrate = 100Mbps;
            eth[2].bitrate = 100Mbps;
            eth[3].bitrate = 100Mbps;
        }

        n2: TsnSwitch {
            @display("p=697.8990822306587,880.5024383035318");
            numEthInterfaces = 3;
            hasOutgoingStreams = true;
            bridging.directionReverser.delayer.typename = "PacketDelayer";
            bridging.directionReverser.delayer.delay = 2000ns;
            eth[*].macLayer.queue.numTrafficClasses = 8;
            eth[0].bitrate = 100Mbps;
            eth[1].bitrate = 100Mbps;
            eth[2].bitrate = 100Mbps;
        }

        n3: TsnSwitch {
            @display("p=744.2888209059747,495.16624796808037");
            numEthInterfaces = 3;
            hasOutgoingStreams = true;
            bridging.directionReverser.delayer.typename = "PacketDelayer";
            bridging.directionReverser.delayer.delay = 2000ns;
            eth[*].macLayer.queue.numTrafficClasses = 8;
            eth[0].bitrate = 100Mbps;
            eth[1].bitrate = 100Mbps;
            eth[2].bitrate = 100Mbps;
        }

        n4: TsnSwitch {
            @display("p=827.8316317128009,655.7410964977093");
            numEthInterfaces = 4;
            hasOutgoingStreams = true;
            bridging.directionReverser.delayer.typename = "PacketDelayer";
            bridging.directionReverser.delayer.delay = 2000ns;
            eth[*].macLayer.queue.numTrafficClasses = 8;
            eth[0].bitrate = 100Mbps;
            eth[1].bitrate = 100Mbps;
            eth[2].bitrate = 100Mbps;
            eth[3].bitrate = 100Mbps;
        }

        n5: TsnSwitch {
            @display("p=896.4100106888799,820.8364119994088");
            numEthInterfaces = 3;
            hasOutgoingStreams = true;
            bridging.directionReverser.delayer.typename = "PacketDelayer";
            bridging.directionReverser.delayer.delay = 2000ns;
            eth[*].macLayer.queue.numTrafficClasses = 8;
            eth[0].bitrate = 100Mbps;
            eth[1].bitrate = 100Mbps;
            eth[2].bitrate = 100Mbps;
        }

        n6: TsnDevice {
            @display("p=369.6620102465814,470.08955223880594");
            numEthInterfaces = 1;
            hasOutgoingStreams = true;
            eth[*].macLayer.queue.numTrafficClasses = 8;
            eth[0].bitrate = 100Mbps;
        }

        n7: TsnDevice {
            @display("p=417.24890346835724,778.9833013152061");
            numEthInterfaces = 1;
            hasOutgoingStreams = true;
            eth[*].macLayer.queue.numTrafficClasses = 8;
            eth[0].bitrate = 100Mbps;
        }

        n8: TsnDevice {
            @display("p=634.9710663079135,1037.2395448500074");
            numEthInterfaces = 1;
            hasOutgoingStreams = true;
            eth[*].macLayer.queue.numTrafficClasses = 8;
            eth[0].bitrate = 100Mbps;
        }

        n9: TsnDevice {
            @display("p=801.8760827098154,337.2395448500074");
            numEthInterfaces = 1;
            hasOutgoingStreams = true;
            eth[*].macLayer.queue.numTrafficClasses = 8;
            eth[0].bitrate = 100Mbps;
        }

        n10: TsnDevice {
            @display("p=1026.2909586819505,596.0336929215309");
            numEthInterfaces = 1;
            hasOutgoingStreams = true;
            eth[*].macLayer.queue.numTrafficClasses = 8;
            eth[0].bitrate = 100Mbps;
        }

        n11: TsnDevice {
            @display("p=1069.6620102465813,909.0113787498152");
            numEthInterfaces = 1;
            hasOutgoingStreams = true;
            eth[*].macLayer.queue.numTrafficClasses = 8;
            eth[0].bitrate = 100Mbps;
        }

    connections:

        n0.ethg[0] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n3.ethg[0];
        n0.ethg[1] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n1.ethg[0];
        n0.ethg[2] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n6.ethg[0];
        n1.ethg[1] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n4.ethg[0];
        n1.ethg[2] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n2.ethg[0];
        n1.ethg[3] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n7.ethg[0];
        n2.ethg[1] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n5.ethg[0];
        n2.ethg[2] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n8.ethg[0];
        n3.ethg[1] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n4.ethg[1];
        n3.ethg[2] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n9.ethg[0];
        n4.ethg[2] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n5.ethg[1];
        n4.ethg[3] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n10.ethg[0];
        n5.ethg[2] <--> EthernetLink { length = 40.0m; datarate = 100Mbps; } <--> n11.ethg[0];
}
