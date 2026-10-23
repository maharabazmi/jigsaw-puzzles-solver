import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const JigsawApp());
}

class JigsawApp extends StatelessWidget {
  const JigsawApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Jigsaw Contour & Assembly AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6366F1),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF0F172A),
        cardTheme: const CardTheme(
          color: Color(0xFF1E293B),
          elevation: 2,
        ),
      ),
      home: const JigsawHomePage(),
    );
  }
}

class JigsawHomePage extends StatefulWidget {
  const JigsawHomePage({super.key});

  @override
  State<JigsawHomePage> createState() => _JigsawHomePageState();
}

class _JigsawHomePageState extends State<JigsawHomePage> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final String _apiBase = "http://127.0.0.1:8000";

  bool _isSolving = false;
  String _statusMessage = "Ready";
  
  final List<Map<String, dynamic>> _samplePuzzles = [
    {"name": "6pieces1.png", "title": "Stone Wall Brick", "pieces": 6, "grid": "2x3"},
    {"name": "6pieces2.png", "title": "Library Portrait", "pieces": 6, "grid": "3x2"},
    {"name": "9pieces3.png", "title": "Holiday Confections", "pieces": 9, "grid": "3x3"},
    {"name": "9pieces1.png", "title": "Classic 9-Piece", "pieces": 9, "grid": "3x3"},
    {"name": "9pieces2.png", "title": "Light Tone Puzzle", "pieces": 9, "grid": "3x3"},
  ];

  late Map<String, dynamic> _selectedSample;
  Map<String, dynamic>? _solverResult;
  Uint8List? _assemblyBytes;
  Uint8List? _montageBytes;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _selectedSample = _samplePuzzles[0];
    _checkServer();
  }

  Future<void> _checkServer() async {
    try {
      final res = await http.get(Uri.parse("$_apiBase/api/health")).timeout(const Duration(seconds: 2));
      if (res.statusCode == 200) {
        setState(() {
          _statusMessage = "Connected to Python Vision Engine";
        });
      }
    } catch (_) {
      setState(() {
        _statusMessage = "Engine Standalone Mode (Start src/api.py for live processing)";
      });
    }
  }

  Future<void> _runSolver() async {
    setState(() {
      _isSolving = true;
      _statusMessage = "Analyzing contours and solving grid...";
    });

    try {
      final response = await http.post(
        Uri.parse("$_apiBase/api/solve"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"sample_name": _selectedSample["name"]}),
      ).timeout(const Duration(seconds: 25));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _solverResult = data;
          if (data["assembly_base64"] != null) {
            _assemblyBytes = base64Decode(data["assembly_base64"]);
          }
          if (data["montage_base64"] != null) {
            _montageBytes = base64Decode(data["montage_base64"]);
          }
          _statusMessage = "Solved in ${data['elapsed_seconds']}s!";
          _isSolving = false;
        });
      } else {
        setState(() {
          _statusMessage = "Solver error: ${response.body}";
          _isSolving = false;
        });
      }
    } catch (e) {
      setState(() {
        _statusMessage = "Could not reach local API. Please run `python -m src.api` in terminal.";
        _isSolving = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.extension_rounded, color: Color(0xFF818CF8), size: 28),
            const SizedBox(width: 12),
            const Text(
              "Jigsaw Contour & Assembly AI",
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20),
            ),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: _statusMessage.contains("Connected")
                    ? const Color(0xFF065F46)
                    : const Color(0xFF334155),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                children: [
                  Icon(
                    _statusMessage.contains("Connected")
                        ? Icons.check_circle_outline
                        : Icons.info_outline,
                    size: 16,
                    color: Colors.white70,
                  ),
                  const SizedBox(width: 6),
                  Text(_statusMessage, style: const TextStyle(fontSize: 12, color: Colors.white70)),
                ],
              ),
            ),
          ],
        ),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: const Color(0xFF818CF8),
          tabs: const [
            Tab(icon: Icon(Icons.grid_view_rounded), text: "Assembly Solution"),
            Tab(icon: Icon(Icons.crop_free_rounded), text: "Segmentation (Step 1)"),
            Tab(icon: Icon(Icons.category_rounded), text: "Edge Classification (Step 2)"),
            Tab(icon: Icon(Icons.handshake_rounded), text: "Matching Matrix (Step 3)"),
          ],
        ),
      ),
      body: Row(
        children: [
          // Left puzzle picker panel
          Container(
            width: 320,
            decoration: const BoxDecoration(
              color: Color(0xFF1E293B),
              border: Border(right: BorderSide(color: Color(0xFF334155))),
            ),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "SELECT PUZZLE IMAGE",
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white54),
                ),
                const SizedBox(height: 12),
                Expanded(
                  child: ListView.separated(
                    itemCount: _samplePuzzles.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, idx) {
                      final item = _samplePuzzles[idx];
                      final isSelected = item["name"] == _selectedSample["name"];
                      return InkWell(
                        onTap: () {
                          setState(() {
                            _selectedSample = item;
                            _solverResult = null;
                            _assemblyBytes = null;
                            _montageBytes = null;
                          });
                        },
                        borderRadius: BorderRadius.circular(10),
                        child: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: isSelected ? const Color(0xFF4F46E5) : const Color(0xFF0F172A),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                              color: isSelected ? const Color(0xFF818CF8) : const Color(0xFF334155),
                            ),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                Icons.image_rounded,
                                color: isSelected ? Colors.white : Colors.white60,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      item["title"],
                                      style: TextStyle(
                                        fontWeight: FontWeight.w600,
                                        color: isSelected ? Colors.white : Colors.white70,
                                      ),
                                    ),
                                    Text(
                                      "${item['name']} • ${item['pieces']} pieces (${item['grid']})",
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: isSelected ? Colors.white70 : Colors.white38,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
                const Divider(color: Color(0xFF334155)),
                const SizedBox(height: 8),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF4F46E5),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    onPressed: _isSolving ? null : _runSolver,
                    icon: _isSolving
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                          )
                        : const Icon(Icons.play_arrow_rounded),
                    label: Text(
                      _isSolving ? "Solving Puzzle..." : "RUN AI SOLVER",
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Main View Tabs
          Expanded(
            child: _solverResult == null
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.auto_fix_high_rounded, size: 64, color: Colors.white24),
                        const SizedBox(height: 16),
                        Text(
                          "Selected: ${_selectedSample['title']} (${_selectedSample['pieces']} pieces)",
                          style: const TextStyle(fontSize: 18, color: Colors.white70),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          "Click 'RUN AI SOLVER' to extract contours and assemble the puzzle.",
                          style: TextStyle(fontSize: 13, color: Colors.white38),
                        ),
                      ],
                    ),
                  )
                : TabBarView(
                    controller: _tabController,
                    children: [
                      _buildAssemblyTab(),
                      _buildSegmentationTab(),
                      _buildClassificationTab(),
                      _buildMatrixTab(),
                    ],
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildAssemblyTab() {
    final solver = _solverResult?["solver"];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _buildStatCard("Total Pieces", "${_solverResult?['piece_count'] ?? 0}", Icons.extension),
              const SizedBox(width: 16),
              _buildStatCard("Grid Layout", "${solver?['rows']} × ${solver?['cols']}", Icons.grid_on),
              const SizedBox(width: 16),
              _buildStatCard("Confidence", "${((solver?['confidence'] ?? 0) * 100).toStringAsFixed(1)}%", Icons.verified),
              const SizedBox(width: 16),
              _buildStatCard("Compute Time", "${_solverResult?['elapsed_seconds']}s", Icons.speed),
            ],
          ),
          const SizedBox(height: 24),
          if (_assemblyBytes != null) ...[
            const Text(
              "ASSEMBLED SOLUTION IMAGE",
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.white60),
            ),
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Container(
                decoration: BoxDecoration(
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: Image.memory(_assemblyBytes!, fit: BoxFit.contain),
              ),
            ),
          ],
          const SizedBox(height: 24),
          const Text(
            "GRID CELL ASSIGNMENTS",
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.white60),
          ),
          const SizedBox(height: 12),
          if (solver?["grid"] != null) ...[
            Column(
              children: [
                for (var row in solver["grid"])
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      children: [
                        for (var cell in row)
                          Expanded(
                            child: Card(
                              child: Padding(
                                padding: const EdgeInsets.all(12),
                                child: Column(
                                  children: [
                                    Text(
                                      "Piece #${cell['piece_id']}",
                                      style: const TextStyle(fontWeight: FontWeight.bold),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      "Rot: ${cell['rotation_deg']}°",
                                      style: const TextStyle(fontSize: 12, color: Colors.white54),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildSegmentationTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            "EXTRACTED PIECES MONTAGE",
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.white60),
          ),
          const SizedBox(height: 12),
          if (_montageBytes != null)
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Container(
                decoration: BoxDecoration(
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: Image.memory(_montageBytes!, fit: BoxFit.contain),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildClassificationTab() {
    final pieces = _solverResult?["pieces"] as List<dynamic>? ?? [];
    return ListView.separated(
      padding: const EdgeInsets.all(24),
      itemCount: pieces.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, idx) {
        final p = pieces[idx];
        final role = p["role"] ?? "UNKNOWN";
        final types = p["types"] as Map<String, dynamic>? ?? {};

        Color roleColor = Colors.green;
        if (role == "CORNER") roleColor = Colors.orange;
        if (role == "BORDER") roleColor = Colors.blue;

        return Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text("Piece #${p['id']}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    const SizedBox(width: 12),
                    Chip(
                      label: Text(role, style: TextStyle(color: roleColor, fontWeight: FontWeight.bold, fontSize: 11)),
                      backgroundColor: roleColor.withOpacity(0.15),
                      side: BorderSide.none,
                      padding: EdgeInsets.zero,
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _buildEdgeBadge("TOP", types["TOP"]),
                    const SizedBox(width: 8),
                    _buildEdgeBadge("RIGHT", types["RIGHT"]),
                    const SizedBox(width: 8),
                    _buildEdgeBadge("BOTTOM", types["BOTTOM"]),
                    const SizedBox(width: 8),
                    _buildEdgeBadge("LEFT", types["LEFT"]),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildEdgeBadge(String side, dynamic type) {
    Color typeColor = Colors.teal;
    if (type == "TAB") typeColor = Colors.amber;
    if (type == "GAP") typeColor = Colors.purpleAccent;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: typeColor.withOpacity(0.4)),
      ),
      child: Text(
        "$side: $type",
        style: TextStyle(color: typeColor, fontSize: 12, fontWeight: FontWeight.w600),
      ),
    );
  }

  Widget _buildMatrixTab() {
    return const Center(
      child: Text(
        "Pairwise Compatibility Matrices computed via MSE on normalized edge curves.",
        style: TextStyle(color: Colors.white54),
      ),
    );
  }

  Widget _buildStatCard(String label, String value, IconData icon) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(icon, color: const Color(0xFF818CF8), size: 28),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: const TextStyle(fontSize: 11, color: Colors.white54)),
                  Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
