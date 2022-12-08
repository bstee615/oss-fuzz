
// Copyright 2022 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
////////////////////////////////////////////////////////////////////////////////

import com.code_intelligence.jazzer.api.FuzzedDataProvider;
import recorder.MyRecordedFuzzedDataProvider;

import com.sun.mail.util.ASCIIUtility;
import java.lang.NumberFormatException;

public class ASCIIUtilityFuzzer {
  public static void fuzzerTestOneInput(FuzzedDataProvider data) {
    try (data = new MyRecordedFuzzedDataProvider(data, "", "ASCIIUtilityFuzzer")) {
    try {
    data.markBeginFuzzer();
    byte[] input = data.consumeRemainingAsBytes();
    try
    {
      ASCIIUtility.parseInt(input, 0, input.length);
      ASCIIUtility.parseLong(input, 0, input.length);
    }
    catch(NumberFormatException e){}

    ASCIIUtility.toString(input);
    } finally { data.markEndFuzzer(); }
    } catch (Exception ex) { }
  }
}
