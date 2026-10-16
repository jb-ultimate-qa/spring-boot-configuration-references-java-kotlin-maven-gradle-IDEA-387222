package demo.single;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class SingleService {
  @Value("${my.key}")                        // RL-02
  String myKey;
}
