// NFC Reader App - Cross Platform (iOS & Android)
import 'package:flutter/material.dart';
import 'package:nfc_manager/nfc_manager.dart';
import 'dart:io';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NFC Reader',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: NFCReaderScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class NFCReaderScreen extends StatefulWidget {
  @override
  _NFCReaderScreenState createState() => _NFCReaderScreenState();
}

class _NFCReaderScreenState extends State<NFCReaderScreen> {
  bool _isAvailable = false;
  bool _isScanning = false;
  String _lastReadData = '';
  String _lastReadType = '';
  List<String> _scanHistory = [];

  @override
  void initState() {
    super.initState();
    _checkNFCAvailability();
  }

  Future<void> _checkNFCAvailability() async {
    bool isAvailable = await NfcManager.instance.isAvailable();
    setState(() {
      _isAvailable = isAvailable;
    });
  }

  Future<void> _startNFCSession() async {
    if (!_isAvailable) {
      _showMessage('NFC is not available on this device');
      return;
    }

    setState(() {
      _isScanning = true;
    });

    try {
      await NfcManager.instance.startSession(
        onDiscovered: (NfcTag tag) async {
          _handleNFCTag(tag);
        },
      );
    } catch (e) {
      setState(() {
        _isScanning = false;
      });
      _showMessage('Error starting NFC session: $e');
    }
  }

  Future<void> _handleNFCTag(NfcTag tag) async {
    try {
      // Handle different NFC technologies
      Map<String, dynamic> techData = {};
      
      // NDEF (NFC Data Exchange Format)
      if (tag.data.containsKey('ndef')) {
        Ndef ndef = Ndef.from(tag);
        if (ndef.isWritable) {
          techData['NDEF'] = 'Writable NDEF tag';
        } else {
          techData['NDEF'] = 'Read-only NDEF tag';
        }
        
        // Read NDEF messages
        NdefMessage? message = await ndef.read();
        if (message != null) {
          for (NdefRecord record in message.records) {
            if (record.typeNameFormat == NdefTypeNameFormat.nfcWellKnown) {
              if (record.type.length > 0 && record.type[0] == 0x54) { // Text record
                String text = _parseTextRecord(record);
                techData['Text'] = text;
              } else if (record.type.length > 0 && record.type[0] == 0x55) { // URL record
                String url = _parseUrlRecord(record);
                techData['URL'] = url;
              }
            }
          }
        }
      }

      // ISO7816 (Smart Card)
      if (tag.data.containsKey('iso7816')) {
        Iso7816 iso7816 = Iso7816.from(tag);
        techData['ISO7816'] = 'Smart Card detected';
      }

      // ISO15693 (Vicinity Card)
      if (tag.data.containsKey('iso15693')) {
        Iso15693 iso15693 = Iso15693.from(tag);
        techData['ISO15693'] = 'Vicinity Card detected';
      }

      // FeliCa (Sony's contactless IC card)
      if (tag.data.containsKey('felica')) {
        Felica felica = Felica.from(tag);
        techData['FeliCa'] = 'FeliCa card detected';
      }

      // Mifare Classic
      if (tag.data.containsKey('mifareclassic')) {
        MifareClassic mifare = MifareClassic.from(tag);
        techData['MifareClassic'] = 'Mifare Classic card detected';
      }

      // Mifare Ultralight
      if (tag.data.containsKey('mifareultralight')) {
        MifareUltralight mifare = MifareUltralight.from(tag);
        techData['MifareUltralight'] = 'Mifare Ultralight card detected';
      }

      // Display the results
      _displayNFCTagData(techData);
      
    } catch (e) {
      _showMessage('Error reading NFC tag: $e');
    } finally {
      await NfcManager.instance.stopSession();
      setState(() {
        _isScanning = false;
      });
    }
  }

  String _parseTextRecord(NdefRecord record) {
    try {
      List<int> payload = record.payload;
      int status = payload[0];
      int languageCodeLength = status & 0x3F;
      String languageCode = String.fromCharCodes(payload.sublist(1, 1 + languageCodeLength));
      String text = String.fromCharCodes(payload.sublist(1 + languageCodeLength));
      return 'Language: $languageCode, Text: $text';
    } catch (e) {
      return 'Unable to parse text record';
    }
  }

  String _parseUrlRecord(NdefRecord record) {
    try {
      List<int> payload = record.payload;
      int prefix = payload[0];
      String url = String.fromCharCodes(payload.sublist(1));
      
      // Add common URL prefixes
      switch (prefix) {
        case 0x01:
          return 'http://www.$url';
        case 0x02:
          return 'https://www.$url';
        case 0x03:
          return 'http://$url';
        case 0x04:
          return 'https://$url';
        default:
          return url;
      }
    } catch (e) {
      return 'Unable to parse URL record';
    }
  }

  void _displayNFCTagData(Map<String, dynamic> techData) {
    String displayData = '';
    String tagType = '';

    techData.forEach((key, value) {
      displayData += '$key: $value\n';
      if (tagType.isEmpty) {
        tagType = key;
      }
    });

    setState(() {
      _lastReadData = displayData.trim();
      _lastReadType = tagType;
      _scanHistory.insert(0, '${DateTime.now().toString().substring(0, 19)} - $tagType');
      if (_scanHistory.length > 10) {
        _scanHistory.removeLast();
      }
    });

    _showMessage('NFC Tag Read Successfully!');
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('NFC Reader'),
        backgroundColor: Colors.blue,
        elevation: 0,
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Colors.blue, Colors.blue.shade50],
          ),
        ),
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Column(
            children: [
              // NFC Status Card
              Card(
                elevation: 8,
                child: Padding(
                  padding: EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      Icon(
                        _isAvailable ? Icons.nfc : Icons.nfc_off,
                        size: 48,
                        color: _isAvailable ? Colors.green : Colors.red,
                      ),
                      SizedBox(height: 8),
                      Text(
                        _isAvailable ? 'NFC Available' : 'NFC Not Available',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: _isAvailable ? Colors.green : Colors.red,
                        ),
                      ),
                      SizedBox(height: 8),
                      Text(
                        Platform.isIOS ? 'iOS Device' : 'Android Device',
                        style: TextStyle(color: Colors.grey),
                      ),
                    ],
                  ),
                ),
              ),
              
              SizedBox(height: 20),
              
              // Scan Button
              SizedBox(
                width: double.infinity,
                height: 60,
                child: ElevatedButton(
                  onPressed: _isAvailable && !_isScanning ? _startNFCSession : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _isScanning ? Colors.orange : Colors.blue,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (_isScanning) ...[
                        SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        ),
                        SizedBox(width: 12),
                      ],
                      Icon(_isScanning ? Icons.nfc : Icons.nfc, color: Colors.white),
                      SizedBox(width: 8),
                      Text(
                        _isScanning ? 'Scanning...' : 'Start NFC Scan',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              
              SizedBox(height: 20),
              
              // Last Read Data
              if (_lastReadData.isNotEmpty) ...[
                Card(
                  elevation: 4,
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.info, color: Colors.blue),
                            SizedBox(width: 8),
                            Text(
                              'Last Read Tag',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        SizedBox(height: 8),
                        Text(
                          'Type: $_lastReadType',
                          style: TextStyle(
                            fontWeight: FontWeight.w500,
                            color: Colors.blue,
                          ),
                        ),
                        SizedBox(height: 8),
                        Text(
                          _lastReadData,
                          style: TextStyle(fontSize: 14),
                        ),
                      ],
                    ),
                  ),
                ),
                SizedBox(height: 20),
              ],
              
              // Scan History
              Expanded(
                child: Card(
                  elevation: 4,
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.history, color: Colors.blue),
                            SizedBox(width: 8),
                            Text(
                              'Scan History',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        SizedBox(height: 8),
                        Expanded(
                          child: _scanHistory.isEmpty
                              ? Center(
                                  child: Text(
                                    'No scans yet',
                                    style: TextStyle(
                                      color: Colors.grey,
                                      fontStyle: FontStyle.italic,
                                    ),
                                  ),
                                )
                              : ListView.builder(
                                  itemCount: _scanHistory.length,
                                  itemBuilder: (context, index) {
                                    return ListTile(
                                      leading: Icon(Icons.nfc, color: Colors.blue),
                                      title: Text(_scanHistory[index]),
                                      dense: true,
                                    );
                                  },
                                ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    NfcManager.instance.stopSession();
    super.dispose();
  }
} 