/*
 * retlang web UI — static local client
 *
 * Bundled QR code generator below.
 * -----------------------------------------------------------------------------
 * QR Code Generator for JavaScript
 *
 * Copyright (c) 2009 Kazuhiko Arase
 *
 * URL: http://www.d-project.com/
 *
 * Licensed under the MIT license:
 *   http://www.opensource.org/licenses/mit-license.php
 *
 * The word "QR Code" is registered trademark of
 * DENSO WAVE INCORPORATED
 *   http://www.denso-wave.com/qrcode/faqpatent-e.html
 * -----------------------------------------------------------------------------
 */
var qrcode = (function () {
  // Compact implementation — 8-bit Byte mode only, QR model 2.
  var qrcode = function (typeNumber, errorCorrectionLevel) {
    var PAD0 = 0xEC;
    var PAD1 = 0x11;
    var _typeNumber = typeNumber;
    var _errorCorrectionLevel = QRErrorCorrectionLevel[errorCorrectionLevel];
    var _modules = null;
    var _moduleCount = 0;
    var _dataCache = null;
    var _dataList = [];
    var _this = {};

    var makeImpl = function (test, maskPattern) {
      _moduleCount = _typeNumber * 4 + 17;
      _modules = (function (moduleCount) {
        var modules = new Array(moduleCount);
        for (var row = 0; row < moduleCount; row += 1) {
          modules[row] = new Array(moduleCount);
          for (var col = 0; col < moduleCount; col += 1) modules[row][col] = null;
        }
        return modules;
      })(_moduleCount);
      setupPositionProbePattern(0, 0);
      setupPositionProbePattern(_moduleCount - 7, 0);
      setupPositionProbePattern(0, _moduleCount - 7);
      setupPositionAdjustPattern();
      setupTimingPattern();
      setupTypeInfo(test, maskPattern);
      if (_typeNumber >= 7) setupTypeNumber(test);
      if (_dataCache == null) _dataCache = createData(_typeNumber, _errorCorrectionLevel, _dataList);
      mapData(_dataCache, maskPattern);
    };

    var setupPositionProbePattern = function (row, col) {
      for (var r = -1; r <= 7; r += 1) {
        if (row + r <= -1 || _moduleCount <= row + r) continue;
        for (var c = -1; c <= 7; c += 1) {
          if (col + c <= -1 || _moduleCount <= col + c) continue;
          if ((0 <= r && r <= 6 && (c == 0 || c == 6)) ||
              (0 <= c && c <= 6 && (r == 0 || r == 6)) ||
              (2 <= r && r <= 4 && 2 <= c && c <= 4)) {
            _modules[row + r][col + c] = true;
          } else {
            _modules[row + r][col + c] = false;
          }
        }
      }
    };

    var getBestMaskPattern = function () {
      var minLostPoint = 0;
      var pattern = 0;
      for (var i = 0; i < 8; i += 1) {
        makeImpl(true, i);
        var lostPoint = QRUtil.getLostPoint(_this);
        if (i == 0 || minLostPoint > lostPoint) { minLostPoint = lostPoint; pattern = i; }
      }
      return pattern;
    };

    var setupTimingPattern = function () {
      for (var r = 8; r < _moduleCount - 8; r += 1) {
        if (_modules[r][6] != null) continue;
        _modules[r][6] = (r % 2 == 0);
      }
      for (var c = 8; c < _moduleCount - 8; c += 1) {
        if (_modules[6][c] != null) continue;
        _modules[6][c] = (c % 2 == 0);
      }
    };

    var setupPositionAdjustPattern = function () {
      var pos = QRUtil.getPatternPosition(_typeNumber);
      for (var i = 0; i < pos.length; i += 1) {
        for (var j = 0; j < pos.length; j += 1) {
          var row = pos[i], col = pos[j];
          if (_modules[row][col] != null) continue;
          for (var r = -2; r <= 2; r += 1) {
            for (var c = -2; c <= 2; c += 1) {
              _modules[row + r][col + c] = (r == -2 || r == 2 || c == -2 || c == 2 || (r == 0 && c == 0));
            }
          }
        }
      }
    };

    var setupTypeNumber = function (test) {
      var bits = QRUtil.getBCHTypeNumber(_typeNumber);
      for (var i = 0; i < 18; i += 1) {
        var mod = (!test && ((bits >> i) & 1) == 1);
        _modules[Math.floor(i / 3)][i % 3 + _moduleCount - 8 - 3] = mod;
      }
      for (var i = 0; i < 18; i += 1) {
        var mod = (!test && ((bits >> i) & 1) == 1);
        _modules[i % 3 + _moduleCount - 8 - 3][Math.floor(i / 3)] = mod;
      }
    };

    var setupTypeInfo = function (test, maskPattern) {
      var data = (_errorCorrectionLevel << 3) | maskPattern;
      var bits = QRUtil.getBCHTypeInfo(data);
      for (var i = 0; i < 15; i += 1) {
        var mod = (!test && ((bits >> i) & 1) == 1);
        if (i < 6) _modules[i][8] = mod;
        else if (i < 8) _modules[i + 1][8] = mod;
        else _modules[_moduleCount - 15 + i][8] = mod;
      }
      for (var i = 0; i < 15; i += 1) {
        var mod = (!test && ((bits >> i) & 1) == 1);
        if (i < 8) _modules[8][_moduleCount - i - 1] = mod;
        else if (i < 9) _modules[8][15 - i - 1 + 1] = mod;
        else _modules[8][15 - i - 1] = mod;
      }
      _modules[_moduleCount - 8][8] = (!test);
    };

    var mapData = function (data, maskPattern) {
      var inc = -1;
      var row = _moduleCount - 1;
      var bitIndex = 7;
      var byteIndex = 0;
      var maskFunc = QRUtil.getMaskFunction(maskPattern);
      for (var col = _moduleCount - 1; col > 0; col -= 2) {
        if (col == 6) col -= 1;
        while (true) {
          for (var c = 0; c < 2; c += 1) {
            if (_modules[row][col - c] == null) {
              var dark = false;
              if (byteIndex < data.length) dark = (((data[byteIndex] >>> bitIndex) & 1) == 1);
              var mask = maskFunc(row, col - c);
              if (mask) dark = !dark;
              _modules[row][col - c] = dark;
              bitIndex -= 1;
              if (bitIndex == -1) { byteIndex += 1; bitIndex = 7; }
            }
          }
          row += inc;
          if (row < 0 || _moduleCount <= row) { row -= inc; inc = -inc; break; }
        }
      }
    };

    var createBytes = function (buffer, rsBlocks) {
      var offset = 0;
      var maxDcCount = 0, maxEcCount = 0;
      var dcdata = new Array(rsBlocks.length), ecdata = new Array(rsBlocks.length);
      for (var r = 0; r < rsBlocks.length; r += 1) {
        var dcCount = rsBlocks[r].dataCount;
        var ecCount = rsBlocks[r].totalCount - dcCount;
        maxDcCount = Math.max(maxDcCount, dcCount);
        maxEcCount = Math.max(maxEcCount, ecCount);
        dcdata[r] = new Array(dcCount);
        for (var i = 0; i < dcdata[r].length; i += 1) dcdata[r][i] = 0xff & buffer.getBuffer()[i + offset];
        offset += dcCount;
        var rsPoly = QRUtil.getErrorCorrectPolynomial(ecCount);
        var rawPoly = qrPolynomial(dcdata[r], rsPoly.getLength() - 1);
        var modPoly = rawPoly.mod(rsPoly);
        ecdata[r] = new Array(rsPoly.getLength() - 1);
        for (var i = 0; i < ecdata[r].length; i += 1) {
          var modIndex = i + modPoly.getLength() - ecdata[r].length;
          ecdata[r][i] = (modIndex >= 0) ? modPoly.getAt(modIndex) : 0;
        }
      }
      var totalCodeCount = 0;
      for (var i = 0; i < rsBlocks.length; i += 1) totalCodeCount += rsBlocks[i].totalCount;
      var data = new Array(totalCodeCount);
      var index = 0;
      for (var i = 0; i < maxDcCount; i += 1) for (var r = 0; r < rsBlocks.length; r += 1) if (i < dcdata[r].length) { data[index] = dcdata[r][i]; index += 1; }
      for (var i = 0; i < maxEcCount; i += 1) for (var r = 0; r < rsBlocks.length; r += 1) if (i < ecdata[r].length) { data[index] = ecdata[r][i]; index += 1; }
      return data;
    };

    var createData = function (typeNumber, errorCorrectionLevel, dataList) {
      var rsBlocks = QRRSBlock.getRSBlocks(typeNumber, errorCorrectionLevel);
      var buffer = qrBitBuffer();
      for (var i = 0; i < dataList.length; i += 1) {
        var data = dataList[i];
        buffer.put(data.getMode(), 4);
        buffer.put(data.getLength(), QRUtil.getLengthInBits(data.getMode(), typeNumber));
        data.write(buffer);
      }
      var totalDataCount = 0;
      for (var i = 0; i < rsBlocks.length; i += 1) totalDataCount += rsBlocks[i].dataCount;
      if (buffer.getLengthInBits() > totalDataCount * 8) {
        throw new Error("code length overflow. (" + buffer.getLengthInBits() + ">" + totalDataCount * 8 + ")");
      }
      if (buffer.getLengthInBits() + 4 <= totalDataCount * 8) buffer.put(0, 4);
      while (buffer.getLengthInBits() % 8 != 0) buffer.putBit(false);
      while (true) {
        if (buffer.getLengthInBits() >= totalDataCount * 8) break;
        buffer.put(PAD0, 8);
        if (buffer.getLengthInBits() >= totalDataCount * 8) break;
        buffer.put(PAD1, 8);
      }
      return createBytes(buffer, rsBlocks);
    };

    _this.addData = function (data) {
      var newData = qr8BitByte(data);
      _dataList.push(newData);
      _dataCache = null;
    };
    _this.isDark = function (row, col) {
      if (row < 0 || _moduleCount <= row || col < 0 || _moduleCount <= col) throw new Error(row + "," + col);
      return _modules[row][col];
    };
    _this.getModuleCount = function () { return _moduleCount; };
    _this.make = function () {
      if (_typeNumber < 1) {
        var typeNumber = 1;
        for (; typeNumber < 40; typeNumber++) {
          var rsBlocks = QRRSBlock.getRSBlocks(typeNumber, _errorCorrectionLevel);
          var buffer = qrBitBuffer();
          for (var i = 0; i < _dataList.length; i++) {
            var data = _dataList[i];
            buffer.put(data.getMode(), 4);
            buffer.put(data.getLength(), QRUtil.getLengthInBits(data.getMode(), typeNumber));
            data.write(buffer);
          }
          var totalDataCount = 0;
          for (var i = 0; i < rsBlocks.length; i++) totalDataCount += rsBlocks[i].dataCount;
          if (buffer.getLengthInBits() <= totalDataCount * 8) break;
        }
        _typeNumber = typeNumber;
      }
      makeImpl(false, getBestMaskPattern());
    };
    return _this;
  };

  var QRMode = { MODE_8BIT_BYTE: 1 << 2 };
  var QRErrorCorrectionLevel = { L: 1, M: 0, Q: 3, H: 2 };
  var QRMaskPattern = { PATTERN000: 0, PATTERN001: 1, PATTERN010: 2, PATTERN011: 3, PATTERN100: 4, PATTERN101: 5, PATTERN110: 6, PATTERN111: 7 };

  var QRUtil = (function () {
    var PATTERN_POSITION_TABLE = [
      [], [6, 18], [6, 22], [6, 26], [6, 30], [6, 34], [6, 22, 38], [6, 24, 42],
      [6, 26, 46], [6, 28, 50], [6, 30, 54], [6, 32, 58], [6, 34, 62], [6, 26, 46, 66],
      [6, 26, 48, 70], [6, 26, 50, 74], [6, 30, 54, 78], [6, 30, 56, 82], [6, 30, 58, 86],
      [6, 34, 62, 90], [6, 28, 50, 72, 94], [6, 26, 50, 74, 98], [6, 30, 54, 78, 102],
      [6, 28, 54, 80, 106], [6, 32, 58, 84, 110], [6, 30, 58, 86, 114], [6, 34, 62, 90, 118],
      [6, 26, 50, 74, 98, 122], [6, 30, 54, 78, 102, 126], [6, 26, 52, 78, 104, 130],
      [6, 30, 56, 82, 108, 134], [6, 34, 60, 86, 112, 138], [6, 30, 58, 86, 114, 142],
      [6, 34, 62, 90, 118, 146], [6, 30, 54, 78, 102, 126, 150], [6, 24, 50, 76, 102, 128, 154],
      [6, 28, 54, 80, 106, 132, 158], [6, 32, 58, 84, 110, 136, 162], [6, 26, 54, 82, 110, 138, 166],
      [6, 30, 58, 86, 114, 142, 170]
    ];
    var G15 = (1 << 10) | (1 << 8) | (1 << 5) | (1 << 4) | (1 << 2) | (1 << 1) | (1 << 0);
    var G18 = (1 << 12) | (1 << 11) | (1 << 10) | (1 << 9) | (1 << 8) | (1 << 5) | (1 << 2) | (1 << 0);
    var G15_MASK = (1 << 14) | (1 << 12) | (1 << 10) | (1 << 4) | (1 << 1);
    var _this = {};
    var getBCHDigit = function (data) {
      var digit = 0;
      while (data != 0) { digit += 1; data >>>= 1; }
      return digit;
    };
    _this.getBCHTypeInfo = function (data) {
      var d = data << 10;
      while (getBCHDigit(d) - getBCHDigit(G15) >= 0) d ^= (G15 << (getBCHDigit(d) - getBCHDigit(G15)));
      return ((data << 10) | d) ^ G15_MASK;
    };
    _this.getBCHTypeNumber = function (data) {
      var d = data << 12;
      while (getBCHDigit(d) - getBCHDigit(G18) >= 0) d ^= (G18 << (getBCHDigit(d) - getBCHDigit(G18)));
      return (data << 12) | d;
    };
    _this.getPatternPosition = function (typeNumber) { return PATTERN_POSITION_TABLE[typeNumber - 1]; };
    _this.getMaskFunction = function (maskPattern) {
      switch (maskPattern) {
        case QRMaskPattern.PATTERN000: return function (i, j) { return (i + j) % 2 == 0; };
        case QRMaskPattern.PATTERN001: return function (i, j) { return i % 2 == 0; };
        case QRMaskPattern.PATTERN010: return function (i, j) { return j % 3 == 0; };
        case QRMaskPattern.PATTERN011: return function (i, j) { return (i + j) % 3 == 0; };
        case QRMaskPattern.PATTERN100: return function (i, j) { return (Math.floor(i / 2) + Math.floor(j / 3)) % 2 == 0; };
        case QRMaskPattern.PATTERN101: return function (i, j) { return (i * j) % 2 + (i * j) % 3 == 0; };
        case QRMaskPattern.PATTERN110: return function (i, j) { return ((i * j) % 2 + (i * j) % 3) % 2 == 0; };
        case QRMaskPattern.PATTERN111: return function (i, j) { return ((i * j) % 3 + (i + j) % 2) % 2 == 0; };
        default: throw new Error("bad maskPattern:" + maskPattern);
      }
    };
    _this.getErrorCorrectPolynomial = function (errorCorrectLength) {
      var a = qrPolynomial([1], 0);
      for (var i = 0; i < errorCorrectLength; i += 1) a = a.multiply(qrPolynomial([1, QRMath.gexp(i)], 0));
      return a;
    };
    _this.getLengthInBits = function (mode, type) {
      if (1 <= type && type < 10) { if (mode == QRMode.MODE_8BIT_BYTE) return 8; }
      else if (type < 27) { if (mode == QRMode.MODE_8BIT_BYTE) return 16; }
      else if (type < 41) { if (mode == QRMode.MODE_8BIT_BYTE) return 16; }
      throw new Error("mode:" + mode + "/type:" + type);
    };
    _this.getLostPoint = function (qr) {
      var moduleCount = qr.getModuleCount();
      var lostPoint = 0;
      for (var row = 0; row < moduleCount; row += 1) {
        for (var col = 0; col < moduleCount; col += 1) {
          var sameCount = 0;
          var dark = qr.isDark(row, col);
          for (var r = -1; r <= 1; r += 1) {
            if (row + r < 0 || moduleCount <= row + r) continue;
            for (var c = -1; c <= 1; c += 1) {
              if (col + c < 0 || moduleCount <= col + c) continue;
              if (r == 0 && c == 0) continue;
              if (dark == qr.isDark(row + r, col + c)) sameCount += 1;
            }
          }
          if (sameCount > 5) lostPoint += (3 + sameCount - 5);
        }
      }
      for (var row = 0; row < moduleCount - 1; row += 1) {
        for (var col = 0; col < moduleCount - 1; col += 1) {
          var count = 0;
          if (qr.isDark(row, col)) count += 1;
          if (qr.isDark(row + 1, col)) count += 1;
          if (qr.isDark(row, col + 1)) count += 1;
          if (qr.isDark(row + 1, col + 1)) count += 1;
          if (count == 0 || count == 4) lostPoint += 3;
        }
      }
      for (var row = 0; row < moduleCount; row += 1) {
        for (var col = 0; col < moduleCount - 6; col += 1) {
          if (qr.isDark(row, col) && !qr.isDark(row, col + 1) && qr.isDark(row, col + 2) && qr.isDark(row, col + 3) && qr.isDark(row, col + 4) && !qr.isDark(row, col + 5) && qr.isDark(row, col + 6)) lostPoint += 40;
        }
      }
      for (var col = 0; col < moduleCount; col += 1) {
        for (var row = 0; row < moduleCount - 6; row += 1) {
          if (qr.isDark(row, col) && !qr.isDark(row + 1, col) && qr.isDark(row + 2, col) && qr.isDark(row + 3, col) && qr.isDark(row + 4, col) && !qr.isDark(row + 5, col) && qr.isDark(row + 6, col)) lostPoint += 40;
        }
      }
      var darkCount = 0;
      for (var col = 0; col < moduleCount; col += 1) for (var row = 0; row < moduleCount; row += 1) if (qr.isDark(row, col)) darkCount += 1;
      var ratio = Math.abs(100 * darkCount / moduleCount / moduleCount - 50) / 5;
      lostPoint += ratio * 10;
      return lostPoint;
    };
    return _this;
  })();

  var QRMath = (function () {
    var EXP_TABLE = new Array(256);
    var LOG_TABLE = new Array(256);
    for (var i = 0; i < 8; i += 1) EXP_TABLE[i] = 1 << i;
    for (var i = 8; i < 256; i += 1) EXP_TABLE[i] = EXP_TABLE[i - 4] ^ EXP_TABLE[i - 5] ^ EXP_TABLE[i - 6] ^ EXP_TABLE[i - 8];
    for (var i = 0; i < 255; i += 1) LOG_TABLE[EXP_TABLE[i]] = i;
    return {
      glog: function (n) { if (n < 1) throw new Error("glog(" + n + ")"); return LOG_TABLE[n]; },
      gexp: function (n) { while (n < 0) n += 255; while (n >= 256) n -= 255; return EXP_TABLE[n]; }
    };
  })();

  function qrPolynomial(num, shift) {
    if (typeof num.length == "undefined") throw new Error(num.length + "/" + shift);
    var _num = (function () {
      var offset = 0;
      while (offset < num.length && num[offset] == 0) offset += 1;
      var _num = new Array(num.length - offset + shift);
      for (var i = 0; i < num.length - offset; i += 1) _num[i] = num[i + offset];
      return _num;
    })();
    var _this = {};
    _this.getAt = function (index) { return _num[index]; };
    _this.getLength = function () { return _num.length; };
    _this.multiply = function (e) {
      var num = new Array(_this.getLength() + e.getLength() - 1);
      for (var i = 0; i < num.length; i += 1) num[i] = 0;
      for (var i = 0; i < _this.getLength(); i += 1) for (var j = 0; j < e.getLength(); j += 1) num[i + j] ^= QRMath.gexp(QRMath.glog(_this.getAt(i)) + QRMath.glog(e.getAt(j)));
      return qrPolynomial(num, 0);
    };
    _this.mod = function (e) {
      if (_this.getLength() - e.getLength() < 0) return _this;
      var ratio = QRMath.glog(_this.getAt(0)) - QRMath.glog(e.getAt(0));
      var num = new Array(_this.getLength());
      for (var i = 0; i < _this.getLength(); i += 1) num[i] = _this.getAt(i);
      for (var i = 0; i < e.getLength(); i += 1) num[i] ^= QRMath.gexp(QRMath.glog(e.getAt(i)) + ratio);
      return qrPolynomial(num, 0).mod(e);
    };
    return _this;
  }

  var QRRSBlock = (function () {
    var RS_BLOCK_TABLE = [
      [1, 26, 19], [1, 26, 16], [1, 26, 13], [1, 26, 9],
      [1, 44, 34], [1, 44, 28], [1, 44, 22], [1, 44, 16],
      [1, 70, 55], [1, 70, 44], [2, 35, 17], [2, 35, 13],
      [1, 100, 80], [2, 50, 32], [2, 50, 24], [4, 25, 9],
      [1, 134, 108], [2, 67, 43], [2, 33, 15, 2, 34, 16], [2, 33, 11, 2, 34, 12],
      [2, 86, 68], [4, 43, 27], [4, 43, 19], [4, 43, 15],
      [2, 98, 78], [4, 49, 31], [2, 32, 14, 4, 33, 15], [4, 39, 13, 1, 40, 14],
      [2, 121, 97], [2, 60, 38, 2, 61, 39], [4, 40, 18, 2, 41, 19], [4, 40, 14, 2, 41, 15],
      [2, 146, 116], [3, 58, 36, 2, 59, 37], [4, 36, 16, 4, 37, 17], [4, 36, 12, 4, 37, 13],
      [2, 86, 68, 2, 87, 69], [4, 69, 43, 1, 70, 44], [6, 43, 19, 2, 44, 20], [6, 43, 15, 2, 44, 16],
      [4, 101, 81], [1, 80, 50, 4, 81, 51], [4, 50, 22, 4, 51, 23], [3, 36, 12, 8, 37, 13],
      [2, 116, 92, 2, 117, 93], [6, 58, 36, 2, 59, 37], [4, 46, 20, 6, 47, 21], [7, 42, 14, 4, 43, 15],
      [4, 133, 107], [8, 59, 37, 1, 60, 38], [8, 44, 20, 4, 45, 21], [12, 33, 11, 4, 34, 12],
      [3, 145, 115, 1, 146, 116], [4, 64, 40, 5, 65, 41], [11, 36, 16, 5, 37, 17], [11, 36, 12, 5, 37, 13],
      [5, 109, 87, 1, 110, 88], [5, 65, 41, 5, 66, 42], [5, 54, 24, 7, 55, 25], [11, 36, 14, 7, 37, 15],
      [5, 122, 98, 1, 123, 99], [7, 73, 45, 3, 74, 46], [15, 43, 19, 2, 44, 20], [3, 45, 15, 13, 46, 16],
      [1, 135, 107, 5, 136, 108], [10, 74, 46, 1, 75, 47], [1, 50, 22, 15, 51, 23], [2, 42, 14, 17, 43, 15],
      [5, 150, 120, 1, 151, 121], [9, 69, 43, 4, 70, 44], [17, 50, 22, 1, 51, 23], [2, 42, 14, 19, 43, 15],
      [3, 141, 113, 4, 142, 114], [3, 70, 44, 11, 71, 45], [17, 47, 21, 4, 48, 22], [9, 39, 13, 16, 40, 14],
      [3, 135, 107, 5, 136, 108], [3, 67, 41, 13, 68, 42], [15, 54, 24, 5, 55, 25], [15, 43, 15, 10, 44, 16],
      [4, 144, 116, 4, 145, 117], [17, 68, 42], [17, 50, 22, 6, 51, 23], [19, 46, 16, 6, 47, 17],
      [2, 139, 111, 7, 140, 112], [17, 74, 46], [7, 54, 24, 16, 55, 25], [34, 37, 13],
      [4, 151, 121, 5, 152, 122], [4, 75, 47, 14, 76, 48], [11, 54, 24, 14, 55, 25], [16, 45, 15, 14, 46, 16],
      [6, 147, 117, 4, 148, 118], [6, 73, 45, 14, 74, 46], [11, 54, 24, 16, 55, 25], [30, 46, 16, 2, 47, 17],
      [8, 132, 106, 4, 133, 107], [8, 75, 47, 13, 76, 48], [7, 54, 24, 22, 55, 25], [22, 45, 15, 13, 46, 16],
      [10, 142, 114, 2, 143, 115], [19, 74, 46, 4, 75, 47], [28, 50, 22, 6, 51, 23], [33, 46, 16, 4, 47, 17],
      [8, 152, 122, 4, 153, 123], [22, 73, 45, 3, 74, 46], [8, 53, 23, 26, 54, 24], [12, 45, 15, 28, 46, 16],
      [3, 147, 117, 10, 148, 118], [3, 73, 45, 23, 74, 46], [4, 54, 24, 31, 55, 25], [11, 45, 15, 31, 46, 16],
      [7, 146, 116, 7, 147, 117], [21, 73, 45, 7, 74, 46], [1, 53, 23, 37, 54, 24], [19, 45, 15, 26, 46, 16],
      [5, 145, 115, 10, 146, 116], [19, 75, 47, 10, 76, 48], [15, 54, 24, 25, 55, 25], [23, 45, 15, 25, 46, 16],
      [13, 145, 115, 3, 146, 116], [2, 74, 46, 29, 75, 47], [42, 54, 24, 1, 55, 25], [23, 45, 15, 28, 46, 16],
      [17, 145, 115], [10, 74, 46, 23, 75, 47], [10, 54, 24, 35, 55, 25], [19, 45, 15, 35, 46, 16],
      [17, 145, 115, 1, 146, 116], [14, 74, 46, 21, 75, 47], [29, 54, 24, 19, 55, 25], [11, 45, 15, 46, 46, 16],
      [13, 145, 115, 6, 146, 116], [14, 74, 46, 23, 75, 47], [44, 54, 24, 7, 55, 25], [59, 46, 16, 1, 47, 17],
      [12, 151, 121, 7, 152, 122], [12, 75, 47, 26, 76, 48], [39, 54, 24, 14, 55, 25], [22, 45, 15, 41, 46, 16],
      [6, 151, 121, 14, 152, 122], [6, 75, 47, 34, 76, 48], [46, 54, 24, 10, 55, 25], [2, 45, 15, 64, 46, 16],
      [17, 152, 122, 4, 153, 123], [29, 74, 46, 14, 75, 47], [49, 54, 24, 10, 55, 25], [24, 45, 15, 46, 46, 16],
      [4, 152, 122, 18, 153, 123], [13, 74, 46, 32, 75, 47], [48, 54, 24, 14, 55, 25], [42, 45, 15, 32, 46, 16],
      [20, 147, 117, 4, 148, 118], [40, 75, 47, 7, 76, 48], [43, 54, 24, 22, 55, 25], [10, 45, 15, 67, 46, 16],
      [19, 148, 118, 6, 149, 119], [18, 75, 47, 31, 76, 48], [34, 54, 24, 34, 55, 25], [20, 45, 15, 61, 46, 16]
    ];
    var qrRSBlock = function (totalCount, dataCount) { return { totalCount: totalCount, dataCount: dataCount }; };
    var _this = {};
    var getRsBlockTable = function (typeNumber, errorCorrectionLevel) {
      switch (errorCorrectionLevel) {
        case QRErrorCorrectionLevel.L: return RS_BLOCK_TABLE[(typeNumber - 1) * 4 + 0];
        case QRErrorCorrectionLevel.M: return RS_BLOCK_TABLE[(typeNumber - 1) * 4 + 1];
        case QRErrorCorrectionLevel.Q: return RS_BLOCK_TABLE[(typeNumber - 1) * 4 + 2];
        case QRErrorCorrectionLevel.H: return RS_BLOCK_TABLE[(typeNumber - 1) * 4 + 3];
        default: return undefined;
      }
    };
    _this.getRSBlocks = function (typeNumber, errorCorrectionLevel) {
      var rsBlock = getRsBlockTable(typeNumber, errorCorrectionLevel);
      if (typeof rsBlock == "undefined") throw new Error("bad rs block @ typeNumber:" + typeNumber + "/errorCorrectionLevel:" + errorCorrectionLevel);
      var length = rsBlock.length / 3;
      var list = [];
      for (var i = 0; i < length; i += 1) {
        var count = rsBlock[i * 3 + 0];
        var totalCount = rsBlock[i * 3 + 1];
        var dataCount = rsBlock[i * 3 + 2];
        for (var j = 0; j < count; j += 1) list.push(qrRSBlock(totalCount, dataCount));
      }
      return list;
    };
    return _this;
  })();

  function qrBitBuffer() {
    var _buffer = [];
    var _length = 0;
    var _this = {};
    _this.getBuffer = function () { return _buffer; };
    _this.getAt = function (index) { var bufIndex = Math.floor(index / 8); return ((_buffer[bufIndex] >>> (7 - index % 8)) & 1) == 1; };
    _this.put = function (num, length) { for (var i = 0; i < length; i += 1) _this.putBit(((num >>> (length - i - 1)) & 1) == 1); };
    _this.getLengthInBits = function () { return _length; };
    _this.putBit = function (bit) {
      var bufIndex = Math.floor(_length / 8);
      if (_buffer.length <= bufIndex) _buffer.push(0);
      if (bit) _buffer[bufIndex] |= (0x80 >>> (_length % 8));
      _length += 1;
    };
    return _this;
  }

  function qr8BitByte(data) {
    var _mode = QRMode.MODE_8BIT_BYTE;
    var _bytes = (function () {
      // UTF-8 encode
      var bytes = [];
      for (var i = 0; i < data.length; i += 1) {
        var c = data.charCodeAt(i);
        if (c < 0x80) bytes.push(c);
        else if (c < 0x800) { bytes.push(0xc0 | (c >> 6)); bytes.push(0x80 | (c & 0x3f)); }
        else if (c < 0xd800 || c >= 0xe000) { bytes.push(0xe0 | (c >> 12)); bytes.push(0x80 | ((c >> 6) & 0x3f)); bytes.push(0x80 | (c & 0x3f)); }
        else {
          i += 1;
          var c2 = 0x10000 + (((c & 0x3ff) << 10) | (data.charCodeAt(i) & 0x3ff));
          bytes.push(0xf0 | (c2 >> 18));
          bytes.push(0x80 | ((c2 >> 12) & 0x3f));
          bytes.push(0x80 | ((c2 >> 6) & 0x3f));
          bytes.push(0x80 | (c2 & 0x3f));
        }
      }
      return bytes;
    })();
    var _this = {};
    _this.getMode = function () { return _mode; };
    _this.getLength = function () { return _bytes.length; };
    _this.write = function (buffer) { for (var i = 0; i < _bytes.length; i += 1) buffer.put(_bytes[i], 8); };
    return _this;
  }

  return qrcode;
})();
/* --- end qrcode-generator ------------------------------------------------- */


/* =========================================================================
   retlang UI
   ========================================================================= */

(() => {
  "use strict";

  const API = {
    encrypt: "/api/encrypt",
    decrypt: "/api/decrypt",
    share:   "/api/share",
    open:    "/api/open",
    suggest: "/api/suggest-phrase",
    strength:"/api/strength",
    alphabets:"/api/alphabets",
  };

  const LS_KEYS = { alphabet: "retlang.alphabet", strength: "retlang.strength" };

  const STRENGTH_LABELS = ["Fast", "Normal", "Strong", "Paranoid"];
  const STRENGTH_META = [
    { iter: 60000,  ms: 18 },
    { iter: 200000, ms: 60 },
    { iter: 600000, ms: 180 },
    { iter: 1800000,ms: 540 },
  ];

  const FALLBACK_ALPHABETS = [
    { id: "base64",         name: "base64",         preview: "ABCDEFGH" },
    { id: "letters",        name: "letters",        preview: "abcdefgh" },
    { id: "numbers",        name: "numbers",        preview: "01234567" },
    { id: "symbols",        name: "symbols",        preview: "!@#$%^&*" },
    { id: "emoji-smiley",   name: "emoji-smiley",   preview: "😀😁😂🤣😃😄😅😆" },
    { id: "emoji-animals",  name: "emoji-animals",  preview: "🐶🐱🐭🐹🐰🦊🐻🐼" },
    { id: "emoji-food",     name: "emoji-food",     preview: "🍎🍐🍊🍋🍌🍉🍇🍓" },
    { id: "emoji-nature",   name: "emoji-nature",   preview: "🌲🌳🌴🌵🌾🌻🌼🌷" },
    { id: "geometric",      name: "geometric",      preview: "●○■□▲△◆◇" },
    { id: "runes",          name: "runes",          preview: "ᚠᚢᚦᚨᚱᚲᚷᚹ" },
    { id: "astro",          name: "astro",          preview: "☀☉☽♁♂♃♄♅" },
  ];

  /* -------------------- DOM references ---------------------------------- */
  const $ = (sel) => document.querySelector(sel);
  const tabs = document.querySelectorAll(".tab");
  const inputText = $("#input-text");
  const inputLabel = $("#input-label");
  const outputLabel = $("#output-label");
  const outputEl = $("#output-text");
  const passInput = $("#passphrase");
  const passToggle = $("#toggle-pass");
  const meterBar = $("#meter-bar");
  const meterVerdict = $("#meter-verdict");
  const meterBits = $("#meter-bits");
  const suggestBtn = $("#suggest-btn");
  const alphabetSeg = $("#alphabet-seg");
  const alphabetPreview = $("#alphabet-preview");
  const strengthInput = $("#strength");
  const strengthCaption = $("#strength-caption");
  const wordmapInput = $("#wordmap");
  const wordmapCaption = $("#wordmap-caption");
  const actionBtn = $("#action-btn");
  const actionLabel = actionBtn.querySelector(".btn-label");
  const copyBtn = $("#copy-btn");
  const qrCanvas = $("#qr-canvas");
  const dropzone = $("#dropzone");
  const toastRegion = $("#toasts");

  /* -------------------- State ------------------------------------------- */
  let state = {
    mode: "encrypt",
    alphabet: localStorage.getItem(LS_KEYS.alphabet) || "base64",
    strength: clampStrength(parseInt(localStorage.getItem(LS_KEYS.strength) || "1", 10)),
    alphabets: FALLBACK_ALPHABETS.slice(),
    lastOutput: "",
    inFlight: false,
  };

  /* -------------------- Tabs -------------------------------------------- */
  tabs.forEach((t) => {
    t.addEventListener("click", () => setMode(t.dataset.mode));
    t.addEventListener("keydown", (e) => {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      e.preventDefault();
      const arr = Array.from(tabs);
      const idx = arr.indexOf(t);
      const nextIdx = e.key === "ArrowRight" ? (idx + 1) % arr.length : (idx - 1 + arr.length) % arr.length;
      arr[nextIdx].focus();
      setMode(arr[nextIdx].dataset.mode);
    });
  });

  function setMode(mode) {
    state.mode = mode;
    tabs.forEach((t) => t.setAttribute("aria-selected", t.dataset.mode === mode ? "true" : "false"));
    const cfg = modeConfig(mode);
    inputLabel.textContent = cfg.inputLabel;
    outputLabel.textContent = cfg.outputLabel;
    inputText.placeholder = cfg.inputPlaceholder;
    actionLabel.textContent = cfg.action;
    // QR only for Share
    qrCanvas.hidden = mode !== "share";
    if (mode !== "share") clearCanvas(qrCanvas);
    clearOutput();
  }

  function modeConfig(mode) {
    switch (mode) {
      case "encrypt": return { inputLabel: "Plaintext", outputLabel: "Ciphertext", inputPlaceholder: "Type or paste text here, or drop a .txt file.", action: "Encrypt \u2192" };
      case "decrypt": return { inputLabel: "Ciphertext", outputLabel: "Plaintext",  inputPlaceholder: "Paste ciphertext here.", action: "Decrypt \u2192" };
      case "share":   return { inputLabel: "Plaintext",  outputLabel: "retlang:// URL", inputPlaceholder: "Type or paste text to share.", action: "Share \u2192" };
      case "open":    return { inputLabel: "retlang:// URL", outputLabel: "Plaintext", inputPlaceholder: "Paste a retlang:// URL here.", action: "Open \u2192" };
    }
    return { inputLabel: "", outputLabel: "", inputPlaceholder: "", action: "Go \u2192" };
  }

  /* -------------------- Passphrase show/hide ---------------------------- */
  passToggle.addEventListener("click", () => {
    const pressed = passToggle.getAttribute("aria-pressed") === "true";
    const next = !pressed;
    passToggle.setAttribute("aria-pressed", String(next));
    passToggle.setAttribute("aria-label", next ? "Hide passphrase" : "Show passphrase");
    passInput.type = next ? "text" : "password";
  });

  /* -------------------- Entropy meter (debounced) ----------------------- */
  let strengthTimer = null;
  passInput.addEventListener("input", () => {
    const v = passInput.value;
    // Instant client-side estimate for snappy feel
    updateMeter(localStrengthEstimate(v));
    if (strengthTimer) clearTimeout(strengthTimer);
    if (!v) return;
    strengthTimer = setTimeout(async () => {
      try {
        const data = await api(API.strength, { passphrase: v });
        updateMeter({
          bits: data.bits,
          score: typeof data.score === "number" ? data.score : null,
          verdict: data.verdict,
          notes: data.notes,
        });
      } catch (_) { /* keep local estimate; backend may be down */ }
    }, 300);
  });

  function updateMeter({ bits, score, verdict }) {
    const pct = Math.max(0, Math.min(100, score != null ? score : Math.min(100, (bits || 0) / 128 * 100)));
    meterBar.style.width = pct + "%";
    meterVerdict.textContent = verdict || verdictFromBits(bits || 0);
    meterBits.textContent = `${Math.round(bits || 0)} bits`;
  }
  function verdictFromBits(b) {
    if (b < 28) return "weak";
    if (b < 40) return "ok";
    if (b < 60) return "good";
    if (b < 90) return "strong";
    return "excellent";
  }
  function localStrengthEstimate(pw) {
    if (!pw) return { bits: 0, verdict: "—", score: 0 };
    let pool = 0;
    if (/[a-z]/.test(pw)) pool += 26;
    if (/[A-Z]/.test(pw)) pool += 26;
    if (/[0-9]/.test(pw)) pool += 10;
    if (/[^a-zA-Z0-9]/.test(pw)) pool += 32;
    const bits = pool ? pw.length * Math.log2(pool) : 0;
    return { bits, verdict: verdictFromBits(bits) };
  }

  /* -------------------- Suggest phrase ---------------------------------- */
  suggestBtn.addEventListener("click", async () => {
    try {
      const data = await api(API.suggest, { words: 6 });
      if (data && data.phrase) {
        passInput.value = data.phrase;
        passInput.dispatchEvent(new Event("input"));
        copyToClipboard(data.phrase).then((ok) => {
          if (ok) toast("Suggested phrase copied", "ok");
          else    toast("Phrase filled");
        });
      } else {
        toast("No phrase returned", "error");
      }
    } catch (e) {
      toast("Could not reach /api/suggest-phrase", "error");
    }
  });

  /* -------------------- Alphabet picker --------------------------------- */
  function renderAlphabets() {
    alphabetSeg.innerHTML = "";
    state.alphabets.forEach((a) => {
      const b = document.createElement("button");
      b.type = "button";
      b.role = "radio";
      b.textContent = a.name;
      b.dataset.id = a.id;
      b.setAttribute("aria-checked", a.id === state.alphabet ? "true" : "false");
      b.addEventListener("click", () => selectAlphabet(a.id));
      b.addEventListener("mouseenter", () => previewAlphabet(a.id));
      b.addEventListener("focus", () => previewAlphabet(a.id));
      b.addEventListener("mouseleave", () => previewAlphabet(state.alphabet));
      b.addEventListener("blur", () => previewAlphabet(state.alphabet));
      alphabetSeg.appendChild(b);
    });
    if (!state.alphabets.find((a) => a.id === state.alphabet)) {
      state.alphabet = state.alphabets[0].id;
    }
    previewAlphabet(state.alphabet);
  }
  function selectAlphabet(id) {
    state.alphabet = id;
    localStorage.setItem(LS_KEYS.alphabet, id);
    Array.from(alphabetSeg.children).forEach((btn) => {
      btn.setAttribute("aria-checked", btn.dataset.id === id ? "true" : "false");
    });
    previewAlphabet(id);
  }
  function previewAlphabet(id) {
    const a = state.alphabets.find((x) => x.id === id);
    if (!a) { alphabetPreview.textContent = "—"; return; }
    const p = (a.preview || "").toString();
    alphabetPreview.textContent = [...p].slice(0, 8).join(" ") || "—";
  }

  /* -------------------- Strength slider --------------------------------- */
  strengthInput.value = String(state.strength);
  updateStrengthCaption();
  strengthInput.addEventListener("input", () => {
    state.strength = clampStrength(parseInt(strengthInput.value, 10));
    localStorage.setItem(LS_KEYS.strength, String(state.strength));
    updateStrengthCaption();
  });
  function updateStrengthCaption() {
    const meta = STRENGTH_META[state.strength];
    strengthCaption.textContent = `${STRENGTH_LABELS[state.strength]} · ~${formatK(meta.iter)} iterations · ~${meta.ms} ms`;
  }
  function clampStrength(n) { if (!Number.isFinite(n)) return 1; return Math.max(0, Math.min(3, n)); }
  function formatK(n) { return n >= 1000 ? Math.round(n / 1000) + "k" : String(n); }

  /* -------------------- Wordmap ---------------------------------------- */
  wordmapInput.addEventListener("input", () => {
    const v = wordmapInput.value.trim();
    if (!v) { wordmapCaption.textContent = "Empty — default wordmap will be used."; wordmapInput.style.borderColor = ""; return; }
    try {
      const parsed = JSON.parse(v);
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) throw new Error("Expected a JSON object");
      const count = Object.keys(parsed).length;
      wordmapCaption.textContent = `Valid JSON · ${count} entries`;
      wordmapInput.style.borderColor = "rgba(52, 211, 153, 0.5)";
    } catch (e) {
      wordmapCaption.textContent = `Invalid JSON: ${e.message}`;
      wordmapInput.style.borderColor = "rgba(248, 113, 113, 0.6)";
    }
  });
  function getWordmap() {
    const v = wordmapInput.value.trim();
    if (!v) return null;
    try {
      const parsed = JSON.parse(v);
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) throw new Error("object");
      return parsed;
    } catch (_) {
      throw new Error("Wordmap is not valid JSON");
    }
  }

  /* -------------------- Action button ---------------------------------- */
  actionBtn.addEventListener("click", submit);
  // Cmd/Ctrl+Enter in input area
  [inputText, passInput, wordmapInput].forEach((el) => {
    el.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        submit();
      }
    });
  });

  async function submit() {
    if (state.inFlight) return;
    const input = inputText.value;
    const pass = passInput.value;
    if (!input) { toast(`Nothing to ${state.mode}`, "error"); inputText.focus(); return; }
    if (state.mode !== "share" /* share could theoretically not need pass on backend, but we enforce */) {
      if (!pass && state.mode !== "share") { toast("Passphrase required", "error"); passInput.focus(); return; }
    }
    if (state.mode === "share" && !pass) { toast("Passphrase required", "error"); passInput.focus(); return; }

    let wordmap = null;
    try { wordmap = getWordmap(); }
    catch (e) { toast(e.message, "error"); return; }

    setLoading(true);
    clearOutput();

    try {
      let result;
      if (state.mode === "encrypt") {
        result = await api(API.encrypt, {
          plaintext: input,
          passphrase: pass,
          alphabet: state.alphabet,
          strength: state.strength,
          wordmap,
        });
        setOutput(result.ciphertext || "");
      } else if (state.mode === "decrypt") {
        result = await api(API.decrypt, {
          ciphertext: input,
          passphrase: pass,
          alphabet: state.alphabet,
          wordmap,
        });
        setOutput(result.plaintext || "");
      } else if (state.mode === "share") {
        result = await api(API.share, {
          plaintext: input,
          passphrase: pass,
          alphabet: state.alphabet,
          strength: state.strength,
          wordmap,
        });
        const url = result.url || "";
        setOutput(url);
        if (url) drawQR(url);
      } else if (state.mode === "open") {
        result = await api(API.open, {
          url: input,
          passphrase: pass,
        });
        setOutput(result.plaintext || "");
      }
    } catch (e) {
      setErrorState(true);
      toast(e.message || "Request failed", "error");
      setTimeout(() => setErrorState(false), 1400);
    } finally {
      setLoading(false);
    }
  }

  function setLoading(on) {
    state.inFlight = on;
    actionBtn.classList.toggle("is-loading", on);
    actionBtn.disabled = on;
  }
  function setErrorState(on) {
    actionBtn.classList.toggle("is-error", on);
  }

  /* -------------------- Output + copy ---------------------------------- */
  function setOutput(text) {
    state.lastOutput = text || "";
    outputEl.textContent = state.lastOutput;
  }
  function clearOutput() {
    state.lastOutput = "";
    outputEl.textContent = "";
    clearCanvas(qrCanvas);
  }
  copyBtn.addEventListener("click", async () => {
    if (!state.lastOutput) { toast("Nothing to copy"); return; }
    const ok = await copyToClipboard(state.lastOutput);
    if (ok) {
      copyBtn.textContent = "Copied \u2713";
      copyBtn.classList.add("is-copied");
      setTimeout(() => { copyBtn.textContent = "Copy"; copyBtn.classList.remove("is-copied"); }, 1500);
    } else {
      toast("Copy failed", "error");
    }
  });
  async function copyToClipboard(text) {
    try {
      if (navigator.clipboard && window.isSecureContext !== false) {
        await navigator.clipboard.writeText(text);
        return true;
      }
    } catch (_) {}
    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      document.body.removeChild(ta);
      return ok;
    } catch (_) { return false; }
  }

  /* -------------------- Drag & drop ------------------------------------- */
  ["dragenter", "dragover"].forEach((ev) =>
    dropzone.addEventListener(ev, (e) => {
      e.preventDefault(); e.stopPropagation();
      dropzone.classList.add("drag-over");
    })
  );
  ["dragleave", "dragend", "drop"].forEach((ev) =>
    dropzone.addEventListener(ev, (e) => {
      e.preventDefault(); e.stopPropagation();
      dropzone.classList.remove("drag-over");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) { toast("File too large (>2 MB)", "error"); return; }
    const reader = new FileReader();
    reader.onload = () => {
      const txt = typeof reader.result === "string" ? reader.result : "";
      inputText.value = txt;
      toast(`Loaded ${file.name}`, "ok");
    };
    reader.onerror = () => toast("Could not read file", "error");
    reader.readAsText(file);
  });

  /* -------------------- QR rendering ----------------------------------- */
  function drawQR(text) {
    try {
      const qr = qrcode(0, "M");
      qr.addData(text);
      qr.make();
      const n = qr.getModuleCount();
      const quiet = 2;
      const scale = 8;
      const size = (n + quiet * 2) * scale;
      qrCanvas.width = size;
      qrCanvas.height = size;
      qrCanvas.style.width = "240px";
      qrCanvas.style.height = "240px";
      qrCanvas.hidden = false;
      const ctx = qrCanvas.getContext("2d");
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, size, size);
      ctx.fillStyle = "#0a0a0f";
      for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
          if (qr.isDark(r, c)) {
            ctx.fillRect((c + quiet) * scale, (r + quiet) * scale, scale, scale);
          }
        }
      }
    } catch (e) {
      toast("QR render failed: " + e.message, "error");
    }
  }
  function clearCanvas(c) {
    if (!c) return;
    const ctx = c.getContext && c.getContext("2d");
    if (ctx) ctx.clearRect(0, 0, c.width, c.height);
  }

  /* -------------------- Toasts ----------------------------------------- */
  function toast(msg, kind) {
    const el = document.createElement("div");
    el.className = "toast" + (kind ? " " + kind : "");
    el.textContent = msg;
    toastRegion.appendChild(el);
    const t = setTimeout(() => dismiss(), 2500);
    function dismiss() {
      clearTimeout(t);
      el.classList.add("leaving");
      setTimeout(() => el.remove(), 220);
    }
    el.addEventListener("click", dismiss);
  }

  /* -------------------- API helper ------------------------------------- */
  async function api(path, body) {
    let resp;
    try {
      resp = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {}),
      });
    } catch (e) {
      throw new Error("Backend unreachable");
    }
    let data = null;
    try { data = await resp.json(); } catch (_) {}
    if (!resp.ok) {
      const msg = (data && data.error) || `HTTP ${resp.status}`;
      throw new Error(msg);
    }
    if (data && data.error) throw new Error(data.error);
    return data || {};
  }

  /* -------------------- Boot ------------------------------------------- */
  async function loadAlphabets() {
    try {
      const data = await api(API.alphabets, {});
      if (data && Array.isArray(data.alphabets) && data.alphabets.length) {
        state.alphabets = data.alphabets.map((a) => ({
          id: a.id || a.name,
          name: a.name || a.id,
          preview: a.preview || "",
        }));
      }
    } catch (_) {
      toast("Using default alphabet list (backend offline)");
    }
    renderAlphabets();
  }

  function boot() {
    setMode("encrypt");
    renderAlphabets();
    loadAlphabets();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
