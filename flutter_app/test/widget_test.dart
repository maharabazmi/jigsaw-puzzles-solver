import 'dart:ui' show Size;

import 'package:flutter_test/flutter_test.dart';
import 'package:jigsaw_solver_app/main.dart';

void main() {
  testWidgets('shows the puzzle selector and default puzzle', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const JigsawApp());

    expect(find.text('Jigsaw Contour & Assembly AI'), findsOneWidget);
    expect(find.text('SELECT PUZZLE IMAGE'), findsOneWidget);
    expect(find.text('Stone Wall Brick'), findsOneWidget);
    expect(find.text('Selected: Stone Wall Brick (6 pieces)'), findsOneWidget);
  });

  testWidgets('selecting a puzzle updates the selected puzzle', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const JigsawApp());
    await tester.tap(find.text('Library Portrait'));
    await tester.pump();

    expect(find.text('Selected: Library Portrait (6 pieces)'), findsOneWidget);
  });
}
