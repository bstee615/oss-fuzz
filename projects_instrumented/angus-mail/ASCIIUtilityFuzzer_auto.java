
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
        //OUTER TRY
        try {
            data = new MyRecordedFuzzedDataProvider(data, "", "ASCIIUtilityFuzzer");
            //INNER TRY
            try {
                ((MyRecordedFuzzedDataProvider) data).markBeginFuzzer();
                byte[] input = data.consumeRemainingAsBytes();
                try {
                    {
                        //transformed code index 1
                        var benjis_result_1 = ASCIIUtility.parseInt(input, 0, input.length);
                        ((MyRecordedFuzzedDataProvider) data).noop(benjis_result_1);
                    }
                    {
                        //transformed code index 2
                        var benjis_result_2 = ASCIIUtility.parseLong(input, 0, input.length);
                        ((MyRecordedFuzzedDataProvider) data).noop(benjis_result_2);
                    }
                } catch (NumberFormatException e) {
                }
                {
                    //transformed code index 0
                    var benjis_result_0 = ASCIIUtility.toString(input);
                    ((MyRecordedFuzzedDataProvider) data).noop(benjis_result_0);
                }
            } finally {
                ((MyRecordedFuzzedDataProvider) data).markEndFuzzer();
                ((MyRecordedFuzzedDataProvider) data).close();
            }
        } catch (Exception ex) {
            throw ex;
        }
    }
}
